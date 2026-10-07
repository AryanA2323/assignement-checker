from typing import List, Tuple
from core.models import QuestionEvaluation
from core.config import Config

class ConfidenceAnalyzer:
    """
    Computes, refines, and audits confidence scores for assignment checking.
    Factors considered:
    1. Handwriting Legibility (clarity of strokes, strokes decipherability)
    2. Transcription Certainty (absence of missing or unreadable tokens)
    3. Rubric Alignment (clear semantic match vs vague/borderline answers)
    4. Model Confidence metrics
    """

    @staticmethod
    def calculate_overall_confidence(
        question_evals: List[QuestionEvaluation],
        threshold: float = Config.MANUAL_REVIEW_THRESHOLD
    ) -> Tuple[float, float, bool, List[str]]:
        """
        Calculates:
        - overall_confidence (0-100)
        - average_legibility (0-100)
        - requires_manual_review (True/False)
        - review_reasons (List of explanations if flagged)
        """
        if not question_evals:
            return 0.0, 0.0, True, ["No questions were evaluated."]

        total_weight = 0.0
        weighted_conf_sum = 0.0
        legibility_sum = 0.0
        review_reasons = []

        for q in question_evals:
            weight = max(q.max_marks, 1.0)
            weighted_conf_sum += q.confidence_score * weight
            total_weight += weight
            legibility_sum += q.legibility_score

            # Check individual question red flags
            if q.confidence_score < 60.0:
                review_reasons.append(
                    f"{q.question_id}: Low evaluation confidence ({q.confidence_score:.1f}%). Possible ambiguous handwriting or borderline answer."
                )
            if q.legibility_score < 55.0:
                review_reasons.append(
                    f"{q.question_id}: Poor handwriting legibility ({q.legibility_score:.1f}%). Verification recommended."
                )

        overall_conf = round(weighted_conf_sum / total_weight, 1)
        avg_legibility = round(legibility_sum / len(question_evals), 1)

        # Global threshold check
        if overall_conf < threshold:
            if not any("Overall" in r for r in review_reasons):
                review_reasons.insert(
                    0,
                    f"Overall evaluation confidence ({overall_conf:.1f}%) is below the safe threshold of {threshold:.0f}%."
                )

        requires_review = len(review_reasons) > 0

        return overall_conf, avg_legibility, requires_review, review_reasons
