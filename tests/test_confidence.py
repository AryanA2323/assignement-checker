import pytest
from core.models import QuestionEvaluation
from core.confidence import ConfidenceAnalyzer

def test_high_confidence_evaluation():
    q1 = QuestionEvaluation(
        question_id="Q1",
        student_transcription="Accurate response",
        marks_awarded=5.0,
        max_marks=5.0,
        confidence_score=95.0,
        legibility_score=90.0,
        feedback="Excellent"
    )
    q2 = QuestionEvaluation(
        question_id="Q2",
        student_transcription="Second accurate response",
        marks_awarded=5.0,
        max_marks=5.0,
        confidence_score=92.0,
        legibility_score=88.0,
        feedback="Very good"
    )

    conf, leg, needs_review, reasons = ConfidenceAnalyzer.calculate_overall_confidence([q1, q2], threshold=70.0)
    assert conf >= 90.0
    assert leg >= 88.0
    assert not needs_review
    assert len(reasons) == 0

def test_low_confidence_triggers_manual_review():
    q1 = QuestionEvaluation(
        question_id="Q1",
        student_transcription="Messy unreadable fragment",
        marks_awarded=1.0,
        max_marks=5.0,
        confidence_score=55.0,  # Below question threshold
        legibility_score=48.0,  # Below legibility threshold
        feedback="Unclear strokes"
    )
    q2 = QuestionEvaluation(
        question_id="Q2",
        student_transcription="Incomplete answer",
        marks_awarded=2.0,
        max_marks=5.0,
        confidence_score=62.0,
        legibility_score=58.0,
        feedback="Lacks details"
    )

    conf, leg, needs_review, reasons = ConfidenceAnalyzer.calculate_overall_confidence([q1, q2], threshold=70.0)
    assert conf < 70.0
    assert needs_review is True
    assert len(reasons) > 0
    # Check that reasons mention low confidence and poor handwriting
    assert any("handwriting" in r.lower() or "legibility" in r.lower() for r in reasons)
