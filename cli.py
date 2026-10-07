import sys
import argparse
from pathlib import Path
from core.config import Config
from core.models import MasterSolution
from core.utils import parse_master_solution_file, export_batch_to_csv
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

    # 1. Load Master Solution
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
        submissions.append({
            "image": str(students_input),
            "file_name": students_input.name
        })
    elif students_input.is_dir():
        for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            for img_file in students_input.glob(ext):
                submissions.append({
                    "image": str(img_file),
                    "file_name": img_file.name
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
        strictness=args.strictness
    )

    # 5. Display Results
    print("\n" + "=" * 76)
    print(f"{'STUDENT EVALUATION SUMMARY REPORT':^76}")
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
    print(f"Class Average Score:      {batch_summary.class_average_score} / {master_solution.total_marks} ({batch_summary.class_average_percentage}%)")
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
