from pydantic import BaseModel


class WeakTopicOut(BaseModel):
    topic_id: str
    topic_name: str
    mastery_probability: float
    attempts_count: int
    recommended_difficulty: int  # what difficulty_from_mastery says to practice at right now


class NextUpTopicOut(BaseModel):
    topic_id: str
    topic_name: str
    sequence_order: int


class RecommendationsOut(BaseModel):
    subject_id: str
    weak_topics: list[WeakTopicOut]
    next_up: list[NextUpTopicOut]
    message: str
