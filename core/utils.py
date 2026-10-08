import io
import json
import csv
from pathlib import Path
from typing import List, Union, Dict, Any
from PIL import Image, ImageOps, ImageEnhance
from core.models import MasterSolution, StudentEvaluation, BatchEvaluationSummary

def optimize_image_for_eval(image_path_or_bytes: Union[str, Path, bytes, Image.Image], max_dimension: int = 1600) -> Image.Image:
    """
    Optimizes a student handwritten image for fast, accurate AI multimodal evaluation:
    - Normalizes orientation using EXIF
    - Converts RGBA/P to RGB
    - Resizes large phone captures (e.g. 4000x3000) down to ~1600px
    - Slightly enhances contrast for faint pencil/ballpoint strokes
    """
    if isinstance(image_path_or_bytes, Image.Image):
        img = image_path_or_bytes.copy()
    elif isinstance(image_path_or_bytes, (str, Path)):
        img = Image.open(image_path_or_bytes)
    else:
        img = Image.open(io.BytesIO(image_path_or_bytes))

    # Fix EXIF orientation (common issue with mobile phone camera uploads)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize if larger than max_dimension
    w, h = img.size
    if max(w, h) > max_dimension:
        ratio = max_dimension / float(max(w, h))
        new_size = (int(w * ratio), int(h * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Slight contrast enhancement to assist faint pencil strokes
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.1)

    return img

def convert_pdf_to_images(pdf_path: Union[str, Path]) -> List[Image.Image]:
    """Extracts pages of a PDF document as PIL Images using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        images = []
        for page in doc:
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)
        return images
    except Exception as e:
        raise RuntimeError(f"Failed to extract images from PDF: {e}")

def stitch_pages_vertically(images: List[Image.Image], max_dimension: int = 2400) -> Image.Image:
    """Stitches multiple page images of a student paper vertically into a single coherent image."""
    if not images:
        raise ValueError("No images provided to stitch.")
    if len(images) == 1:
        return optimize_image_for_eval(images[0], max_dimension=max_dimension)

    target_width = 1200
    resized = []
    total_height = 0
    for img in images:
        w, h = img.size
        ratio = target_width / float(w)
        new_h = int(h * ratio)
        res = img.resize((target_width, new_h), Image.Resampling.LANCZOS)
        resized.append(res)
        total_height += new_h

    stitched = Image.new("RGB", (target_width, total_height), (255, 255, 255))
    curr_y = 0
    for r in resized:
        stitched.paste(r, (0, curr_y))
        curr_y += r.height

    if total_height > max_dimension:
        ratio = max_dimension / float(total_height)
        stitched = stitched.resize((int(target_width * ratio), max_dimension), Image.Resampling.LANCZOS)

    return stitched

def parse_master_solution_file(file_path: Union[str, Path]) -> MasterSolution:
    """Parses a Master Solution from JSON, text, markdown, or PDF file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Master solution file not found: {file_path}")

    # If it is a PDF file, check sibling JSON or extract text using fitz
    if path.suffix.lower() == ".pdf":
        json_sibling = path.with_suffix(".json")
        if json_sibling.exists():
            with open(json_sibling, "r", encoding="utf-8") as f:
                return MasterSolution.from_dict(json.load(f))
        try:
            import fitz
            doc = fitz.open(path)
            content = "\n".join(page.get_text() for page in doc)
            return parse_text_master_solution(content)
        except Exception as e:
            raise RuntimeError(f"Could not extract text from Master PDF: {e}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        data = json.loads(content)
        return MasterSolution.from_dict(data)
    except json.JSONDecodeError:
        # Fallback to simple markdown/text parser
        return parse_text_master_solution(content)

def parse_text_master_solution(text: str) -> MasterSolution:
    """Parses simple plain-text or markdown format master solutions."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    title = "Assignment Master Solution"
    subject = "General"
    questions = []
    
    current_q = None
    for line in lines:
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
        elif line.startswith("Q") and ":" in line:
            if current_q:
                questions.append(current_q)
            q_id, rest = line.split(":", 1)
            current_q = {
                "question_id": q_id.strip(),
                "question_text": rest.strip(),
                "max_marks": 5.0,
                "model_answer": "",
                "key_concepts": []
            }
        elif current_q and line.lower().startswith("marks:"):
            try:
                current_q["max_marks"] = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif current_q and line.lower().startswith("answer:"):
            current_q["model_answer"] = line.split(":", 1)[1].strip()
        elif current_q and line.lower().startswith("keys:"):
            current_q["key_concepts"] = [k.strip() for k in line.split(":", 1)[1].split(",")]
        elif current_q and not current_q["model_answer"]:
            current_q["model_answer"] += (" " + line)

    if current_q:
        questions.append(current_q)

    if not questions:
        # Dummy single question if parsing was empty
        questions = [{
            "question_id": "Q1",
            "question_text": "Answer the assignment question",
            "max_marks": 10.0,
            "model_answer": text,
            "key_concepts": []
        }]

    total_marks = sum(q["max_marks"] for q in questions)
    return MasterSolution(
        title=title,
        subject=subject,
        total_marks=total_marks,
        questions=questions
    )

def export_batch_to_csv(batch: BatchEvaluationSummary, output_path: Union[str, Path]) -> str:
    """Exports batch evaluation results to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Student ID", "Student Name", "File", "Total Score", "Max Marks",
            "Percentage (%)", "Confidence Score (%)", "Legibility (%)",
            "Needs Manual Review", "Review Notes", "Feedback Summary"
        ])
        for s in batch.results:
            writer.writerow([
                s.student_id,
                s.student_name,
                s.file_name,
                s.total_score,
                s.max_possible_score,
                f"{s.percentage:.1f}",
                f"{s.overall_confidence_score:.1f}",
                f"{s.average_legibility:.1f}",
                "YES" if s.requires_manual_review else "NO",
                "; ".join(s.review_reasons),
                s.summary_feedback
            ])
    return str(path)
