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

@app.route("/api/evaluate", methods=["POST"])
def evaluate():
    """
    Main evaluation endpoint.
    Handles master solution (preset demo, uploaded file, or raw text)
    and student assignments (demo files, uploaded images, or multi-page PDFs).
    """
    global LAST_EVALUATION

    strictness = request.form.get("strictness", "standard").lower()
    force_mock = request.form.get("force_mock", "false").lower() == "true"
    use_demo_master = request.form.get("use_demo_master", "false").lower() == "true"
    use_demo_students = request.form.get("use_demo_students", "false").lower() == "true"

    # 1. Resolve Master Solution
    master_solution = None
    if use_demo_master:
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
        # Default fallback to demo master
        master_path = Config.DEMO_DIR / "master_solution.json"
        if master_path.exists():
            master_solution = parse_master_solution_file(master_path)
        else:
            return jsonify({"error": "No master solution provided."}), 400

    # 2. Resolve Student Submissions
    submissions = []
    if use_demo_students:
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
                # Convert PDF pages into images
                try:
                    images = convert_pdf_to_images(dest_path)
                    for i, page_img in enumerate(images):
                        page_filename = f"{Path(filename).stem}_page{i+1}.png"
                        page_path = Config.UPLOAD_DIR / page_filename
                        page_img.save(page_path, "PNG")
                        submissions.append({
                            "image": page_img,
                            "file_name": page_filename,
                            "preview_url": f"/uploads/{page_filename}"
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
            strictness=strictness
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
