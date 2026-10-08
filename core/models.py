from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class QuestionMaster(BaseModel):
    """Definition of a question within the master answer key."""
    question_id: str = Field(..., description="Unique question identifier (e.g. Q1, Q2a)")
    question_text: str = Field(..., description="The full text of the question")
    max_marks: float = Field(..., description="Maximum marks allocated for this question", ge=0.5)
    model_answer: str = Field(..., description="Ideal/Master answer or reference explanation")
    key_concepts: List[str] = Field(default_factory=list, description="Mandatory concepts/keywords required")
    grading_rubric: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Optional breakdown: e.g. {'full': 'All points covered', 'partial': 'Only definition'}"
    )

class MasterSolution(BaseModel):
    """The master reference solution against which student papers are evaluated."""
    title: str = Field(..., description="Title of the assignment or test")
    subject: Optional[str] = Field("General", description="Subject or topic area")
    total_marks: float = Field(..., description="Sum of maximum marks across all questions")
    instructions: Optional[str] = Field("", description="Special grading instructions or lenient rules")
    questions: List[QuestionMaster] = Field(..., description="List of questions in the assignment")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MasterSolution":
        return cls(**data)

class QuestionEvaluation(BaseModel):
    """Evaluation result for an individual question on a student's paper."""
    question_id: str
    student_transcription: str = Field(..., description="Transcribed student handwritten answer")
    marks_awarded: float = Field(..., description="Marks given to the student", ge=0)
    max_marks: float = Field(..., description="Maximum possible marks for this question")
    confidence_score: float = Field(..., description="Confidence of checking accuracy (0-100)", ge=0, le=100)
    legibility_score: float = Field(..., description="Estimated readability of student's handwriting (0-100)", ge=0, le=100)
    key_concepts_covered: List[str] = Field(default_factory=list)
    missing_concepts: List[str] = Field(default_factory=list)
    feedback: str = Field(..., description="Constructive feedback explaining mark allocation")
    teacher_rationale: Optional[str] = Field(None, description="Detailed explanation for teacher audit")

class StudentEvaluation(BaseModel):
    """Comprehensive evaluation report for one student's handwritten assignment."""
    student_id: str
    student_name: str
    file_name: str
    total_score: float = Field(..., ge=0)
    max_possible_score: float = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)
    overall_confidence_score: float = Field(..., description="Aggregated confidence score (0-100)", ge=0, le=100)
    average_legibility: float = Field(..., description="Average handwriting legibility (0-100)", ge=0, le=100)
    requires_manual_review: bool = Field(False, description="Flagged for teacher manual review if confidence is low")
    review_reasons: List[str] = Field(default_factory=list, description="Reasons why manual review is recommended")
    question_evaluations: List[QuestionEvaluation] = Field(default_factory=list)
    summary_feedback: str = Field("", description="Overall teacher summary feedback for the student")
    evaluation_mode: str = Field("master_solution", description="Evaluation mode: 'master_solution' or 'ai_direct'")
    evaluation_time_seconds: float = Field(0.0, description="Processing duration in seconds")
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

class BatchEvaluationSummary(BaseModel):
    """Summary of batch evaluation across multiple students."""
    total_submissions: int
    evaluated_count: int
    class_average_score: float
    class_average_percentage: float
    average_confidence: float
    flagged_for_review_count: int
    evaluation_mode: str = Field("master_solution", description="Evaluation mode: 'master_solution' or 'ai_direct'")
    processing_time_total_seconds: float
    results: List[StudentEvaluation]
