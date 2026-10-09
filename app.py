import os
import io
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename

from core.config import Config
from core.models import MasterSolution, BatchEvaluationSummary
from core.utils import (
    optimize_image_for_eval,
    convert_pdf_to_images,
    stitch_pages_vertically,
    parse_master_solution_file,
    parse_text_master_solution,
    export_batch_to_csv,
)
from core.evaluator import AssignmentEvaluator

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB max upload

# Store the last evaluation in memory for export
LAST_EVALUATION = None

@app.route("/")
def index():
    """Serves the main web dashboard."""
    return render_template("index.html")

@app.route("/static/demo/<path:filename>")
def serve_demo_file(filename):
    """Serves demo student handwriting images and files."""
    demo_dir = Config.BASE_DIR / "static" / "demo"
    return send_from_directory(str(demo_dir), filename)

@app.route("/uploads/<path:filename>")
def serve_upload_file(filename):
    """Serves uploaded submission files for browser preview."""
    return send_from_directory(str(Config.UPLOAD_DIR), filename)

@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns system status, active model, and API key presence."""
    has_key = Config.has_api_key()
    masked_key = ""
    if has_key:
        k = Config.GEMINI_API_KEY
        masked_key = k[:4] + "*" * (len(k) - 8) + k[-4:] if len(k) > 8 else "***"

    return jsonify({
        "has_api_key": has_key,
        "masked_key": masked_key,
        "model_name": Config.GEMINI_MODEL,
        "default_strictness": Config.DEFAULT_STRICTNESS,
        "review_threshold": Config.MANUAL_REVIEW_THRESHOLD
    })

@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Updates API key and runtime configuration."""
    data = request.get_json() or {}
    new_key = data.get("gemini_api_key")
    if new_key is not None:
        Config.set_api_key(new_key.strip())

    if "model_name" in data and data["model_name"]:
        Config.GEMINI_MODEL = data["model_name"].strip()
    if "review_threshold" in data:
        try:
            Config.MANUAL_REVIEW_THRESHOLD = float(data["review_threshold"])
        except ValueError:
            pass

    return jsonify({
        "success": True,
        "has_api_key": Config.has_api_key(),
        "model_name": Config.GEMINI_MODEL,
        "review_threshold": Config.MANUAL_REVIEW_THRESHOLD
    })

@app.route("/api/test-gemini", methods=["POST"])
def test_gemini():
    """Tests Gemini API key connectivity."""
    data = request.get_json() or {}
    key_to_test = data.get("api_key") or Config.GEMINI_API_KEY
    if not key_to_test:
        return jsonify({"success": False, "message": "No API key provided."}), 400

    try:
        from google import genai
        client = genai.Client(api_key=key_to_test)
        response = client.models.generate_content(
            model=Config.GEMINI_MODEL,
            contents="Say 'API connection successful' in 3 words."
        )
        return jsonify({
            "success": True,
            "message": "Connected successfully to Gemini!",
            "reply": response.text.strip()
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Connection error: {str(e)}"}), 400

@app.route("/api/demo/master", methods=["GET"])
def get_demo_master():
    """Returns the demo master solution JSON."""
    master_path = Config.DEMO_DIR / "master_solution.json"
    if not master_path.exists():
        return jsonify({"error": "Demo master solution not found"}), 404
    with open(master_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

@app.route("/api/sample/info", methods=["GET"])
def get_sample_info():
    """Returns metadata about the bundled CS 545 college assignment dataset."""
    return jsonify({
        "success": True,
        "course": "CS 545: Advanced Distributed Systems",
        "assignment": "Assignment 1 — Consensus, Concurrency & Fault Tolerance",
        "total_marks": 50,
        "master_file": "ass_1/master_solution.pdf",
        "students": [
            {"name": "Alex Chen", "file": "student_1_alex_chen.pdf", "pages": 3, "handwriting": "Fountain pen (Neat proofs)"},
            {"name": "Priya Sharma", "file": "student_2_priya_sharma.pdf", "pages": 3, "handwriting": "Ballpoint pen (Authentic college handwriting)"},
            {"name": "Marcus Vance", "file": "student_3_marcus_vance.pdf", "pages": 3, "handwriting": "Gel pen (Slanted/Flagged for manual review)"}
        ]
    })

@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """
    Main evaluation endpoint.
    Handles master solution (preset demo, uploaded file, or raw text)
    and student assignments (demo files, uploaded images, or multi-page PDFs).
    """
    global LAST_EVALUATION

    json_data = request.get_json(silent=True) or {}
    def get_param(key, default=""):
        if key in request.form:
            return request.form.get(key, default)
        return json_data.get(key, default)

    strictness = str(get_param("strictness", "standard")).lower()
    force_mock = str(get_param("force_mock", "false")).lower() == "true"
    use_demo_master = str(get_param("use_demo_master", "false")).lower() == "true"
    use_demo_students = str(get_param("use_demo_students", "false")).lower() == "true"
    use_sample_ass1 = str(get_param("use_sample_ass1", "false")).lower() == "true"
    evaluation_mode = str(get_param("evaluation_mode", "master_solution")).lower()
    subject_or_topic = str(get_param("subject_or_topic", "")).strip() or None

    # 1. Resolve Master Solution (Not required if evaluation_mode == 'ai_direct')
    master_solution = None
    if evaluation_mode == "ai_direct":
        master_solution = None
    elif use_sample_ass1:
        ass1_master = Path("ass_1/master_solution.pdf")
        if ass1_master.exists():
            master_solution = parse_master_solution_file(ass1_master)
        else:
            master_solution = parse_master_solution_file(Config.DEMO_DIR / "master_solution.json")
    elif use_demo_master:
        master_path = Config.DEMO_DIR / "master_solution.json"
        master_solution = parse_master_solution_file(master_path)
    elif "master_file" in request.files and request.files["master_file"].filename:
        mf = request.files["master_file"]
        filename = secure_filename(mf.filename)
        dest_path = Config.UPLOAD_DIR / f"master_{filename}"
        mf.save(dest_path)
        master_solution = parse_master_solution_file(dest_path)
    elif request.form.get("master_text"):
        master_solution = parse_text_master_solution(request.form.get("master_text"))
    else:
        # Default fallback to demo master if in master_solution mode
        master_path = Config.DEMO_DIR / "master_solution.json"
        if master_path.exists():
            master_solution = parse_master_solution_file(master_path)
        else:
            return jsonify({"error": "No master solution provided for Master Solution mode."}), 400

    # 2. Resolve Student Submissions
    submissions = []
    if use_sample_ass1:
        ass1_dir = Path("ass_1")
        for pdf_name in ["student_1_alex_chen.pdf", "student_2_priya_sharma.pdf", "student_3_marcus_vance.pdf"]:
            pdf_path = ass1_dir / pdf_name
            if pdf_path.exists():
                images = convert_pdf_to_images(pdf_path)
                stitched_img = stitch_pages_vertically(images)
                preview_name = f"{pdf_path.stem}_preview.jpg"
                preview_dest = Config.UPLOAD_DIR / preview_name
                stitched_img.save(preview_dest, "JPEG", quality=85)
                submissions.append({
                    "image": stitched_img,
                    "file_name": pdf_name,
                    "preview_url": f"/uploads/{preview_name}"
                })
    elif use_demo_students:
        demo_students_dir = Config.DEMO_DIR / "students"
        for img_file in sorted(demo_students_dir.glob("*.png")):
            submissions.append({
                "image": str(img_file),
                "file_name": img_file.name,
                "preview_url": f"/static/demo/{img_file.name}"
            })
    else:
        uploaded_files = request.files.getlist("student_files")
        for f in uploaded_files:
            if not f or not f.filename:
                continue
            filename = secure_filename(f.filename)
            ext = Path(filename).suffix.lower()
            dest_path = Config.UPLOAD_DIR / filename
            f.save(dest_path)

            if ext == ".pdf":
                try:
                    images = convert_pdf_to_images(dest_path)
                    stitched_img = stitch_pages_vertically(images)
                    stitched_filename = f"{Path(filename).stem}_preview.jpg"
                    stitched_path = Config.UPLOAD_DIR / stitched_filename
                    stitched_img.save(stitched_path, "JPEG", quality=85)
                    submissions.append({
                        "image": stitched_img,
                        "file_name": filename,
                        "preview_url": f"/uploads/{stitched_filename}"
                    })
                except Exception as e:
                    return jsonify({"error": f"Failed to process PDF {filename}: {str(e)}"}), 400
            elif ext in Config.ALLOWED_IMAGE_EXTENSIONS:
                submissions.append({
                    "image": str(dest_path),
                    "file_name": filename,
                    "preview_url": f"/uploads/{filename}"
                })

    if not submissions:
        return jsonify({"error": "No student assignment files provided to evaluate."}), 400

    # 3. Perform Evaluation
    evaluator = AssignmentEvaluator()
    try:
        # Mark force_mock in items if requested
        if force_mock:
            for s in submissions:
                s["force_mock"] = True

        batch_result = evaluator.evaluate_batch(
            submissions=submissions,
            master_solution=master_solution,
            strictness=strictness,
            evaluation_mode=evaluation_mode,
            subject_or_topic=subject_or_topic
        )
        
        # Attach preview URLs to results
        result_dicts = []
        for i, res in enumerate(batch_result.results):
            d = res.model_dump()
            # Link matching preview url
            for s in submissions:
                if s["file_name"] == res.file_name:
                    d["preview_url"] = s.get("preview_url")
                    break
            result_dicts.append(d)

        output_data = batch_result.model_dump()
        output_data["results"] = result_dicts
        output_data["is_live_gemini"] = evaluator.is_live and not force_mock
        output_data["model_used"] = evaluator.model_name if (evaluator.is_live and not force_mock) else "Mock Engine"
        output_data["evaluation_mode"] = evaluation_mode

        LAST_EVALUATION = batch_result
        return jsonify(output_data)

    except Exception as e:
        return jsonify({"error": f"Evaluation error: {str(e)}"}), 500

@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    """Exports latest evaluation as CSV download."""
    global LAST_EVALUATION
    if not LAST_EVALUATION:
        return jsonify({"error": "No recent evaluation found to export."}), 400

    csv_path = Config.REPORTS_DIR / "latest_evaluation.csv"
    export_batch_to_csv(LAST_EVALUATION, csv_path)
    return send_file(
        str(csv_path),
        mimetype="text/csv",
        as_attachment=True,
        download_name="assignment_evaluation_report.csv"
    )

@app.route("/api/export/json", methods=["GET"])
def export_json():
    """Exports latest evaluation as JSON download."""
    global LAST_EVALUATION
    if not LAST_EVALUATION:
        return jsonify({"error": "No recent evaluation found to export."}), 400

    json_path = Config.REPORTS_DIR / "latest_evaluation.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(LAST_EVALUATION.model_dump(), f, indent=2)

    return send_file(
        str(json_path),
        mimetype="application/json",
        as_attachment=True,
        download_name="assignment_evaluation_report.json"
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    print(f"\n========================================================")
    print(f" AI Handwritten Assignment Checker Server Started")
    print(f" Dashboard URL: http://127.0.0.1:{port}")
    print(f" Live Gemini Vision: {'ACTIVE' if Config.has_api_key() else 'OFFLINE (Mock Mode Active)'}")
    print(f"========================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
