from pydantic import BaseModel


class QuizNextRequest(BaseModel):
    topic_id: str


class QuizNextResponse(BaseModel):
    question_id: str
    topic_id: str
    difficulty_level: int
    question_type: str
    prompt: str
    choices: list[str] | None = None
    freshly_generated: bool  # True if the LLM just generated this question on the fly


class QuizSubmitRequest(BaseModel):
    question_id: str
    user_answer: str
    response_time_seconds: float | None = None


class QuizSubmitResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    explanation: str | None = None
    mastery_probability: float
    attempts_count: int
    correct_count: int
    next_difficulty_level: int  # what get_next_question would return right now, for UI preview
