from datetime import datetime

from pydantic import BaseModel


class AssessmentStartRequest(BaseModel):
    subject_id: str


class AssessmentQuestionOut(BaseModel):
    """A question shown to the learner during the diagnostic — no correct_answer field."""

    id: str
    topic_id: str
    difficulty_level: int
    question_type: str
    prompt: str
    choices: list[str] | None = None

    model_config = {"from_attributes": True}


class AssessmentStartResponse(BaseModel):
    assessment_id: str
    subject_id: str
    questions: list[AssessmentQuestionOut]


class AssessmentAnswer(BaseModel):
    question_id: str
    user_answer: str
    response_time_seconds: float | None = None


class AssessmentSubmitRequest(BaseModel):
    answers: list[AssessmentAnswer]


class TopicMasteryResult(BaseModel):
    topic_id: str
    topic_name: str
    correct: int
    total: int
    mastery_probability: float


class AssessmentSubmitResponse(BaseModel):
    assessment_id: str
    status: str
    overall_score: float
    topic_results: list[TopicMasteryResult]


class AssessmentOut(BaseModel):
    id: str
    subject_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
