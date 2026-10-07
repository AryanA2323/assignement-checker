import pytest
from pathlib import Path
from PIL import Image
from core.models import MasterSolution
from core.utils import parse_master_solution_file, optimize_image_for_eval
from core.evaluator import AssignmentEvaluator

@pytest.fixture
def sample_master():
    path = Path("demo_data/master_solution.json")
    return parse_master_solution_file(path)

def test_image_optimizer():
    # Create test high-res image
    img = Image.new("RGB", (3000, 2000), (255, 255, 255))
    optimized = optimize_image_for_eval(img, max_dimension=1200)
    w, h = optimized.size
    assert max(w, h) <= 1200

def test_evaluator_mock_alice(sample_master):
    evaluator = AssignmentEvaluator()
    alice_img = Path("demo_data/students/student_alice.png")
    assert alice_img.exists()

    result = evaluator.evaluate_submission(
        image_or_path=alice_img,
        master_solution=sample_master,
        file_name="student_alice.png",
        force_mock=True
    )

    assert result.student_name == "Alice Johnson"
    assert result.total_score >= 18.0
    assert result.percentage >= 90.0
    assert result.overall_confidence_score >= 90.0
    assert not result.requires_manual_review
    assert len(result.question_evaluations) == len(sample_master.questions)

def test_evaluator_mock_charlie_flagged(sample_master):
    evaluator = AssignmentEvaluator()
    charlie_img = Path("demo_data/students/student_charlie.png")
    assert charlie_img.exists()

    result = evaluator.evaluate_submission(
        image_or_path=charlie_img,
        master_solution=sample_master,
        file_name="student_charlie.png",
        force_mock=True
    )

    assert result.student_name == "Charlie Davis"
    assert result.total_score < 12.0
    assert result.overall_confidence_score < 70.0
    assert result.requires_manual_review is True
    assert len(result.review_reasons) > 0

def test_batch_evaluation(sample_master):
    evaluator = AssignmentEvaluator()
    subs = [
        {"image": "demo_data/students/student_alice.png", "file_name": "student_alice.png", "force_mock": True},
        {"image": "demo_data/students/student_bob.png", "file_name": "student_bob.png", "force_mock": True},
        {"image": "demo_data/students/student_charlie.png", "file_name": "student_charlie.png", "force_mock": True}
    ]
    batch = evaluator.evaluate_batch(subs, sample_master)
    assert batch.total_submissions == 3
    assert batch.flagged_for_review_count == 1
    assert batch.class_average_score > 0
