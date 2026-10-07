import io
import json
import time
from typing import List, Optional, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

from core.config import Config
from core.models import (
    MasterSolution,
    QuestionEvaluation,
    StudentEvaluation,
    BatchEvaluationSummary,
)
from core.confidence import ConfidenceAnalyzer
from core.utils import optimize_image_for_eval

class AssignmentEvaluator:
    """
    Multimodal Handwritten Assignment Evaluator.
    Evaluates handwritten images/PDFs against a Master Solution using Gemini Multimodal Vision API,
    with an intelligent fallback simulator when running offline or in unit tests.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model_name = model or Config.GEMINI_MODEL
        self._client = None

        if self.api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[AssignmentEvaluator] Warning: Could not initialize Gemini client: {e}")
                self._client = None

    @property
    def is_live(self) -> bool:
        """True if live Gemini API client is initialized and ready."""
        return self._client is not None

    def evaluate_submission(
        self,
        image_or_path: Union[str, Path, Image.Image, bytes],
        master_solution: MasterSolution,
        file_name: str = "submission.png",
        student_id_hint: Optional[str] = None,
        student_name_hint: Optional[str] = None,
        strictness: str = "standard",
        force_mock: bool = False
    ) -> StudentEvaluation:
        """
        Evaluates a single student handwritten assignment against the master solution.
        """
        start_time = time.time()

        # Optimize image
        if isinstance(image_or_path, Image.Image):
            pil_image = image_or_path
        else:
            pil_image = optimize_image_for_eval(image_or_path)

        # Decide whether to use Live Gemini or Mock
        if not force_mock and self.is_live:
            evaluation = self._evaluate_with_gemini(
                pil_image, master_solution, file_name,
                student_id_hint, student_name_hint, strictness
            )
        else:
            evaluation = self._evaluate_with_mock(
                pil_image, master_solution, file_name,
                student_id_hint, student_name_hint, strictness
            )

        evaluation.evaluation_time_seconds = round(time.time() - start_time, 2)
        return evaluation

    def evaluate_batch(
        self,
        submissions: List[dict],
        master_solution: MasterSolution,
        strictness: str = "standard",
        max_workers: int = 4
    ) -> BatchEvaluationSummary:
        """
        Evaluates multiple student assignments concurrently for minimal total processing time.
        Each submission item: {'image': ..., 'file_name': ..., 'name': ..., 'id': ...}
        """
        start_time = time.time()
        results: List[StudentEvaluation] = []

        def _worker(sub):
            return self.evaluate_submission(
                image_or_path=sub["image"],
                master_solution=master_solution,
                file_name=sub.get("file_name", "student.png"),
                student_id_hint=sub.get("id"),
                student_name_hint=sub.get("name"),
                strictness=strictness,
                force_mock=sub.get("force_mock", False)
            )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_worker, sub) for sub in submissions]
            for f in futures:
                results.append(f.result())

        total_submissions = len(results)
        evaluated_count = len(results)
        class_avg_score = round(sum(r.total_score for r in results) / total_submissions, 2) if results else 0.0
        class_avg_pct = round(sum(r.percentage for r in results) / total_submissions, 1) if results else 0.0
        avg_conf = round(sum(r.overall_confidence_score for r in results) / total_submissions, 1) if results else 0.0
        flagged_count = sum(1 for r in results if r.requires_manual_review)
        total_time = round(time.time() - start_time, 2)

        return BatchEvaluationSummary(
            total_submissions=total_submissions,
            evaluated_count=evaluated_count,
            class_average_score=class_avg_score,
            class_average_percentage=class_avg_pct,
            average_confidence=avg_conf,
            flagged_for_review_count=flagged_count,
            processing_time_total_seconds=total_time,
            results=results
        )

    def _build_evaluation_prompt(self, master: MasterSolution, strictness: str) -> str:
        """Constructs a structured prompt instructing Gemini to grade handwritten work."""
        questions_text = []
        for q in master.questions:
            questions_text.append(
                f"- Question ID: {q.question_id}\n"
                f"  Text: {q.question_text}\n"
                f"  Max Marks: {q.max_marks}\n"
                f"  Model Answer: {q.model_answer}\n"
                f"  Key Required Concepts: {', '.join(q.key_concepts)}\n"
                f"  Rubric: {json.dumps(q.grading_rubric or {})}"
            )

        strictness_guide = {
            "lenient": "Be generous with partial credit. If the core idea is conveyed despite grammatical or minor terminology errors, award majority of marks.",
            "standard": "Fair academic grading. Require main key concepts. Award proportional partial credit for partially correct reasoning.",
            "strict": "High rigor. Deduct marks for omitted technical keywords, incomplete definitions, or lack of precision."
        }.get(strictness, "Standard fair academic grading.")

        return f"""
You are an expert academic evaluator. Your task is to evaluate a handwritten student answer sheet image against the official Master Solution key.

MASTER SOLUTION TITLE: {master.title}
SUBJECT: {master.subject}
TOTAL POSSIBLE MARKS: {master.total_marks}
GRADING STRICTNESS: {strictness.upper()} ({strictness_guide})

MASTER QUESTIONS & ANSWERS:
{chr(10).join(questions_text)}

EVALUATION INSTRUCTIONS:
1. Inspect the handwritten image carefully. Read the student's handwritten responses for each question.
2. If student name or roll number/student ID is written at the top, transcribe it. Otherwise, return null or fallback.
3. For each question:
   a. Transcribe the student's handwritten answer accurately into 'student_transcription'. If unreadable or blank, indicate so.
   b. Assess correctness against the Master Solution.
   c. Award 'marks_awarded' as a float between 0.0 and the question's Max Marks.
   d. Rate 'legibility_score' from 0.0 to 100.0 (how easy or hard the student's handwriting was to read).
   e. Rate 'confidence_score' from 0.0 to 100.0 (how confident you are in your grading accuracy, factoring in handwriting clarity, ambiguity, and completeness).
   f. Identify which 'key_concepts_covered' were present and which 'missing_concepts' were absent.
   g. Provide concise, constructive 'feedback' explaining why marks were awarded or deducted.
4. Calculate the overall percentage and provide a motivating summary feedback.

CRITICAL: Return ONLY a valid JSON object matching this schema. Do NOT include markdown fences, preamble, or any text other than raw JSON:
{{
  "student_name": "Transcribed student name or null",
  "student_id": "Transcribed ID or null",
  "question_evaluations": [
    {{
      "question_id": "Q1",
      "student_transcription": "Transcribed text...",
      "marks_awarded": 4.5,
      "max_marks": 5.0,
      "confidence_score": 95.0,
      "legibility_score": 90.0,
      "key_concepts_covered": ["concept1", "concept2"],
      "missing_concepts": [],
      "feedback": "Clear explanation covering all requirements.",
      "teacher_rationale": "Awarded full credit as both definitions match master."
    }}
  ],
  "summary_feedback": "Overall performance summary..."
}}
"""

    def _evaluate_with_gemini(
        self,
        image: Image.Image,
        master: MasterSolution,
        file_name: str,
        student_id_hint: Optional[str],
        student_name_hint: Optional[str],
        strictness: str
    ) -> StudentEvaluation:
        """Calls Gemini 2.5 Flash Vision API with structured JSON output."""
        from google.genai import types

        prompt = self._build_evaluation_prompt(master, strictness)

        # Convert PIL image to bytes buffer
        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        image_bytes = buf.getvalue()

        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            prompt
        ]

        config = types.GenerateContentConfig(
            temperature=0.1,  # Low temperature for deterministic grading
            response_mime_type="application/json"
        )

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            raw_text = response.text.strip()
            data = json.loads(raw_text)
        except Exception as e:
            raise RuntimeError(f"Gemini API evaluation failed: {e}")

        # Parse question evaluations
        q_evals: List[QuestionEvaluation] = []
        for q_data in data.get("question_evaluations", []):
            q_evals.append(QuestionEvaluation(
                question_id=q_data["question_id"],
                student_transcription=q_data.get("student_transcription", ""),
                marks_awarded=float(q_data.get("marks_awarded", 0.0)),
                max_marks=float(q_data.get("max_marks", 5.0)),
                confidence_score=float(q_data.get("confidence_score", 85.0)),
                legibility_score=float(q_data.get("legibility_score", 85.0)),
                key_concepts_covered=q_data.get("key_concepts_covered", []),
                missing_concepts=q_data.get("missing_concepts", []),
                feedback=q_data.get("feedback", ""),
                teacher_rationale=q_data.get("teacher_rationale")
            ))

        total_score = round(sum(q.marks_awarded for q in q_evals), 2)
        max_possible = round(sum(q.max_marks for q in q_evals), 2) or master.total_marks
        pct = round((total_score / max_possible * 100.0) if max_possible > 0 else 0.0, 1)

        # Analyze confidence
        overall_conf, avg_leg, needs_review, reasons = ConfidenceAnalyzer.calculate_overall_confidence(q_evals)

        student_name = student_name_hint or data.get("student_name") or Path(file_name).stem.replace("_", " ").title()
        student_id = student_id_hint or data.get("student_id") or f"STU-{abs(hash(file_name)) % 10000:04d}"

        return StudentEvaluation(
            student_id=student_id,
            student_name=student_name,
            file_name=file_name,
            total_score=total_score,
            max_possible_score=max_possible,
            percentage=pct,
            overall_confidence_score=overall_conf,
            average_legibility=avg_leg,
            requires_manual_review=needs_review,
            review_reasons=reasons,
            question_evaluations=q_evals,
            summary_feedback=data.get("summary_feedback", "Evaluation completed successfully.")
        )

    def _evaluate_with_mock(
        self,
        image: Image.Image,
        master: MasterSolution,
        file_name: str,
        student_id_hint: Optional[str],
        student_name_hint: Optional[str],
        strictness: str
    ) -> StudentEvaluation:
        """
        Intelligent Mock Engine:
        Provides realistic simulation based on student profile (Alice=Top, Bob=Average, Charlie=Struggling/Messy).
        Ensures 100% testability and instant offline demo capability without waiting for API keys.
        """
        stem = Path(file_name).stem.lower()
        strictness_factor = {"lenient": 1.05, "standard": 1.0, "strict": 0.95}.get(strictness, 1.0)

        if "charlie" in stem or "low" in stem:
            # Charlie: Struggling student, messy handwriting, low confidence
            student_name = student_name_hint or "Charlie Davis"
            student_id = student_id_hint or "STU-1003"
            target_ratio = 0.40 * strictness_factor
            legibility = 52.0
            base_conf = 62.0
            transcriptions = {
                "Q1": "Supervised learn is when data has labels. Machine learn learns patterns.",
                "Q2": "Overfiting happens when train score is too high. Stop training maybe.",
                "Q3": "CNN is convolution neural net for photos. RNN is recursive.",
                "Q4": "Gradient descent minimizes error using math steps."
            }
        elif "bob" in stem or "medium" in stem or "average" in stem:
            # Bob: Decent student, average handwriting, missing a few keywords
            student_name = student_name_hint or "Bob Martinez"
            student_id = student_id_hint or "STU-1002"
            target_ratio = 0.74 * strictness_factor
            legibility = 82.0
            base_conf = 88.0
            transcriptions = {
                "Q1": "Supervised learning uses labeled training datasets to map inputs to outputs. Unsupervised learning finds hidden groupings or patterns in unlabeled datasets.",
                "Q2": "Overfitting happens when a model learns noise in training data and fails on new test data. We can prevent it using regularization or dropout.",
                "Q3": "CNNs use convolutional layers for spatial 2D data like images. RNNs process sequential data using internal loops.",
                "Q4": "Gradient descent is an optimization algorithm that iteratively adjusts weights in the direction of steepest descent of the loss function."
            }
        else:
            # Alice (default): Excellent student, neat handwriting, high confidence
            student_name = student_name_hint or "Alice Johnson"
            student_id = student_id_hint or "STU-1001"
            target_ratio = 0.94 * strictness_factor
            legibility = 95.0
            base_conf = 96.0
            transcriptions = {
                "Q1": "Supervised learning trains algorithms on labeled data with known ground truth targets to predict future outcomes. In contrast, unsupervised learning discovers inherent patterns, clusters, and structures in unlabeled datasets without explicit guidance.",
                "Q2": "Overfitting occurs when a statistical model learns both underlying signals and random noise in the training set, causing high training accuracy but poor generalization on unseen validation data. Mitigations include L1/L2 regularization, early stopping, cross-validation, and data augmentation.",
                "Q3": "CNN (Convolutional Neural Network) employs shared kernels and spatial hierarchies specifically designed for grid-like data such as images. RNN (Recurrent Neural Network) maintains hidden recurrent states to handle variable-length sequential time-series or linguistic data.",
                "Q4": "Gradient descent is a first-order iterative optimization algorithm used to find local minima of a differentiable loss function by taking proportional steps negative to the gradient vector."
            }

        q_evals: List[QuestionEvaluation] = []
        for i, q in enumerate(master.questions):
            # Proportional marks with slight variation
            marks = round(min(q.max_marks, max(0.0, q.max_marks * target_ratio)), 1)
            # Question specific confidence
            q_conf = min(100.0, max(45.0, base_conf + (i % 3 - 1) * 3.0))
            q_leg = min(100.0, max(40.0, legibility + (i % 2 - 0.5) * 4.0))

            covered = []
            missing = []
            for kc in q.key_concepts:
                if target_ratio >= 0.75 or (target_ratio >= 0.5 and len(covered) < len(q.key_concepts) // 2 + 1):
                    covered.append(kc)
                else:
                    missing.append(kc)

            feedback_text = (
                f"Demonstrated good understanding of the core topic. Covered: {', '.join(covered)}."
                if not missing
                else f"Partial credit awarded. Missing key concepts: {', '.join(missing)}."
            )

            tx = transcriptions.get(q.question_id, f"Answer for {q.question_id} transcribed from student paper.")

            q_evals.append(QuestionEvaluation(
                question_id=q.question_id,
                student_transcription=tx,
                marks_awarded=marks,
                max_marks=q.max_marks,
                confidence_score=round(q_conf, 1),
                legibility_score=round(q_leg, 1),
                key_concepts_covered=covered,
                missing_concepts=missing,
                feedback=feedback_text,
                teacher_rationale=f"Simulated evaluation against rubric (Strictness: {strictness})."
            ))

        total_score = round(sum(q.marks_awarded for q in q_evals), 2)
        max_possible = round(sum(q.max_marks for q in q_evals), 2) or master.total_marks
        pct = round((total_score / max_possible * 100.0) if max_possible > 0 else 0.0, 1)

        overall_conf, avg_leg, needs_review, reasons = ConfidenceAnalyzer.calculate_overall_confidence(q_evals)

        summary_note = (
            "Outstanding submission! Highly legible handwriting and accurate understanding of concepts."
            if pct >= 85
            else "Good overall performance with minor conceptual gaps to review."
            if pct >= 60
            else "Needs improvement. Handwriting clarity was low and key concepts were omitted. Recommended for teacher review."
        )

        return StudentEvaluation(
            student_id=student_id,
            student_name=student_name,
            file_name=file_name,
            total_score=total_score,
            max_possible_score=max_possible,
            percentage=pct,
            overall_confidence_score=overall_conf,
            average_legibility=avg_leg,
            requires_manual_review=needs_review,
            review_reasons=reasons,
            question_evaluations=q_evals,
            summary_feedback=summary_note
        )
