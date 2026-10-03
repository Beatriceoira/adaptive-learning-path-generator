from pydantic import BaseModel


class TopicMasterySnapshot(BaseModel):
    topic_id: str
    topic_name: str
    mastery_probability: float
    attempts_count: int
    correct_count: int
    is_weak_topic: bool


class ProgressOverview(BaseModel):
    subject_id: str
    topics_total: int
    topics_mastered: int  # live count: mastery_probability >= MASTERY_THRESHOLD right now
    overall_accuracy: float | None  # None if there have been zero attempts anywhere in the subject
    total_attempts: int
    total_correct: int
    weak_topic_count: int
    # Snapshot from the active roadmap's step statuses at the time it was (re)generated --
    # not live. A learner who practices after generating a roadmap can push mastery past
    # the threshold for a topic without this number moving until they regenerate it.
    roadmap_completion_pct: float | None
    topic_mastery: list[TopicMasterySnapshot]


class DailyActivity(BaseModel):
    date: str  # YYYY-MM-DD
    attempts: int
    correct: int


class ProgressHistory(BaseModel):
    subject_id: str
    days: int
    daily_activity: list[DailyActivity]  # one entry per day in the window, zero-filled gaps included
