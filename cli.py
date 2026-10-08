import sys
import argparse
from pathlib import Path
from core.config import Config
from core.models import MasterSolution
from core.utils import (
    parse_master_solution_file,
    export_batch_to_csv,
    convert_pdf_to_images,
    stitch_pages_vertically,
)
from core.evaluator import AssignmentEvaluator

def print_banner():
    banner = r"""
========================================================================
   AI HANDWRITTEN ASSIGNMENT CHECKER & CONFIDENCE EVALUATOR
========================================================================
    """
    print(banner)

def main():
    print_banner()
    parser = argparse.ArgumentParser(
        description="Automatically evaluate handwritten student assignments against a master solution key."
    )
    parser.add_argument(
        "--master", "-m",
        type=str,
        default="demo_data/master_solution.json",
        help="Path to Master Solution file (.json or .txt)"
    )
    parser.add_argument(
        "--ai-direct",
        action="store_true",
        help="Check directly with AI using real Google data without requiring a master solution"
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="Optional subject or domain hint for AI Direct evaluation (e.g., 'Distributed Systems')"
    )
    parser.add_argument(
        "--students", "-s",
        type=str,
        default="demo_data/students",
        help="Path to student image file, PDF, or directory of student submissions"
    )
    parser.add_argument(
        "--strictness",
        choices=["lenient", "standard", "strict"],
        default="standard",
        help="Grading strictness level (default: standard)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Gemini API key (overrides .env)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force mock evaluation mode for offline testing"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="reports/evaluation_results.csv",
        help="File path to save CSV/JSON report"
    )

    args = parser.parse_args()

    # 1. Master Solution / Mode Resolution
    master_solution = None
    evaluation_mode = "ai_direct" if args.ai_direct else "master_solution"

    if args.ai_direct:
        print("[*] Mode: Autonomous AI Direct Evaluation (Evaluating directly with real Google / academic knowledge)")
        if args.subject:
            print(f"[*] Subject Context: {args.subject}")
        master_path = None
    else:
        master_path = Path(args.master)
        if not master_path.exists():
            print(f"[-] Error: Master solution not found at {master_path}")
            sys.exit(1)

        print(f"[*] Loading Master Solution: {master_path}")
        master_solution = parse_master_solution_file(master_path)
        print(f"[+] Loaded: '{master_solution.title}' with {len(master_solution.questions)} questions (Total Marks: {master_solution.total_marks})")

    # 2. Gather Student Submissions
    students_input = Path(args.students)
    submissions = []
    if students_input.is_file():
        if students_input.suffix.lower() == ".pdf":
            imgs = convert_pdf_to_images(students_input)
            submissions.append({
                "image": stitch_pages_vertically(imgs),
                "file_name": students_input.name
            })
        else:
            submissions.append({
                "image": str(students_input),
                "file_name": students_input.name
            })
    elif students_input.is_dir():
        for file_path in sorted(students_input.iterdir()):
            if "master" in file_path.name.lower() or (master_path and file_path.resolve() == master_path.resolve()):
                continue
            ext = file_path.suffix.lower()
            if ext == ".pdf":
                imgs = convert_pdf_to_images(file_path)
                submissions.append({
                    "image": stitch_pages_vertically(imgs),
                    "file_name": file_path.name
                })
            elif ext in (".png", ".jpg", ".jpeg", ".webp"):
                submissions.append({
                    "image": str(file_path),
                    "file_name": file_path.name
                })
    else:
        print(f"[-] Error: Student path not found: {students_input}")
        sys.exit(1)

    if not submissions:
        print(f"[-] Error: No valid image files found in {students_input}")
        sys.exit(1)

    print(f"[*] Found {len(submissions)} student submission(s) to evaluate.")

    # 3. Initialize Evaluator
    api_key = args.api_key or Config.GEMINI_API_KEY
    evaluator = AssignmentEvaluator(api_key=api_key)
    
    if evaluator.is_live and not args.mock:
        print(f"[+] Active Engine: Live Gemini Multimodal AI ({evaluator.model_name})")
    else:
        print("[!] Active Engine: Offline / Mock Evaluation Simulator (No live Gemini API key provided or --mock enabled)")

    # 4. Run Batch Evaluation
    print("[*] Starting fast batch evaluation...")
    batch_summary = evaluator.evaluate_batch(
        submissions=submissions,
        master_solution=master_solution,
        strictness=args.strictness,
        force_mock=args.mock,
        evaluation_mode=evaluation_mode,
        subject_or_topic=args.subject
    )

    # 5. Display Results
    header_title = "DIRECT AI EVALUATION REPORT (GOOGLE DATA)" if evaluation_mode == "ai_direct" else "STUDENT EVALUATION SUMMARY REPORT"
    print("\n" + "=" * 76)
    print(f"{header_title:^76}")
    print("=" * 76)
    print(f"{'Student Name':<20} | {'Score':<10} | {'Pct':<7} | {'Confidence':<12} | {'Legibility':<10} | {'Status':<10}")
    print("-" * 76)

    for res in batch_summary.results:
        status = "NEEDS REVIEW" if res.requires_manual_review else "VERIFIED"
        score_str = f"{res.total_score}/{res.max_possible_score}"
        print(
            f"{res.student_name:<20} | {score_str:<10} | {res.percentage:>5.1f}% | "
            f"{res.overall_confidence_score:>9.1f}% | {res.average_legibility:>8.1f}% | {status:<10}"
        )

    print("-" * 76)
    total_max = master_solution.total_marks if master_solution else (batch_summary.results[0].max_possible_score if batch_summary.results else 50.0)
    print(f"Class Average Score:      {batch_summary.class_average_score} / {total_max} ({batch_summary.class_average_percentage}%)")
    print(f"Average AI Confidence:    {batch_summary.average_confidence}%")
    print(f"Submissions Flagged:      {batch_summary.flagged_for_review_count} / {batch_summary.total_submissions}")
    print(f"Total Processing Time:    {batch_summary.processing_time_total_seconds}s")
    print("=" * 76)

    # Detailed question breakdowns
    for res in batch_summary.results:
        print(f"\n--- Detailed Breakdown: {res.student_name} ({res.file_name}) ---")
        if res.requires_manual_review:
            print("  [!] Flagged Reasons:")
            for r in res.review_reasons:
                print(f"      * {r}")
        for q in res.question_evaluations:
            print(f"  [{q.question_id}] Awarded: {q.marks_awarded}/{q.max_marks} (Conf: {q.confidence_score}%, Leg: {q.legibility_score}%)")
            print(f"      Transcription: {q.student_transcription[:90]}...")
            print(f"      Feedback:      {q.feedback}")

    # 6. Export Report
    out_file = export_batch_to_csv(batch_summary, args.output)
    print(f"\n[+] Full detailed CSV report exported to: {out_file}\n")

if __name__ == "__main__":
    main()
