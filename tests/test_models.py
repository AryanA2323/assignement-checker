import pytest
from core.models import QuestionMaster, MasterSolution, QuestionEvaluation, StudentEvaluation

def test_question_master_creation():
    q = QuestionMaster(
        question_id="Q1",
        question_text="What is machine learning?",
        max_marks=5.0,
        model_answer="Machine learning is a subfield of artificial intelligence.",
        key_concepts=["artificial intelligence", "data-driven"]
    )
    assert q.question_id == "Q1"
    assert q.max_marks == 5.0
    assert len(q.key_concepts) == 2

def test_master_solution_from_dict():
    data = {
        "title": "Exam 1",
        "subject": "CS",
        "total_marks": 10.0,
        "questions": [
            {
                "question_id": "Q1",
                "question_text": "Define AI.",
                "max_marks": 5.0,
                "model_answer": "AI is artificial intelligence.",
                "key_concepts": ["intelligence"]
            },
            {
                "question_id": "Q2",
                "question_text": "Define ML.",
                "max_marks": 5.0,
                "model_answer": "ML is machine learning.",
                "key_concepts": ["learning"]
            }
        ]
    }
    ms = MasterSolution.from_dict(data)
    assert ms.title == "Exam 1"
    assert len(ms.questions) == 2
    assert ms.total_marks == 10.0

def test_student_evaluation_model():
    q_eval = QuestionEvaluation(
        question_id="Q1",
        student_transcription="AI is intelligence.",
        marks_awarded=4.5,
        max_marks=5.0,
        confidence_score=92.0,
        legibility_score=88.0,
        key_concepts_covered=["intelligence"],
        missing_concepts=[],
        feedback="Good answer"
    )
    student = StudentEvaluation(
        student_id="STU-01",
        student_name="Alice",
        file_name="alice.png",
        total_score=4.5,
        max_possible_score=5.0,
        percentage=90.0,
        overall_confidence_score=92.0,
        average_legibility=88.0,
        requires_manual_review=False,
        question_evaluations=[q_eval]
    )
    assert student.total_score == 4.5
    assert not student.requires_manual_review
    assert student.percentage == 90.0
