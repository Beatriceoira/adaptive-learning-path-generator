"""
Aggregates existing state into the two views the progress dashboard needs:

- an overview snapshot (per-topic mastery, overall accuracy, weak-topic
  count, roadmap completion) -- everything here is derived live from
  `mastery_scores` except roadmap_completion_pct, which reflects the active
  roadmap's step statuses as of whenever it was last generated
- a daily activity history (attempts/correct per day) from `quiz_attempts`,
  which already holds both diagnostic and practice answers -- zero-filled
  so every day in the window has an entry, which keeps a chart's x-axis
  continuous instead of skipping inactive days
"""

from datetime import datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import LearningPath, LearningPathStep, MasteryScore, QuizAttempt, Topic
from app.schemas.progress import DailyActivity, ProgressHistory, ProgressOverview, TopicMasterySnapshot
from app.services.roadmap import MASTERY_THRESHOLD


def get_progress_overview(db: Session, user_id: str, subject_id: str) -> ProgressOverview:
    topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()
    topic_ids = [t.id for t in topics]

    mastery_by_topic = {
        m.topic_id: m
        for m in db.query(MasteryScore)
        .filter(MasteryScore.user_id == user_id, MasteryScore.topic_id.in_(topic_ids))
        .all()
    }

    topic_mastery = [
        TopicMasterySnapshot(
            topic_id=t.id,
            topic_name=t.name,
            mastery_probability=mastery_by_topic[t.id].mastery_probability if t.id in mastery_by_topic else 0.0,
            attempts_count=mastery_by_topic[t.id].attempts_count if t.id in mastery_by_topic else 0,
            correct_count=mastery_by_topic[t.id].correct_count if t.id in mastery_by_topic else 0,
            is_weak_topic=mastery_by_topic[t.id].is_weak_topic if t.id in mastery_by_topic else False,
        )
        for t in topics
    ]

    total_attempts = sum(tm.attempts_count for tm in topic_mastery)
    total_correct = sum(tm.correct_count for tm in topic_mastery)
    overall_accuracy = round(total_correct / total_attempts, 3) if total_attempts else None
    topics_mastered = sum(1 for tm in topic_mastery if tm.mastery_probability >= MASTERY_THRESHOLD)
    weak_topic_count = sum(1 for tm in topic_mastery if tm.is_weak_topic)

    active_path = (
        db.query(LearningPath)
        .filter(
            LearningPath.user_id == user_id,
            LearningPath.subject_id == subject_id,
            LearningPath.is_active == True,  # noqa: E712
        )
        .first()
    )
    roadmap_completion_pct = None
    if active_path:
        steps = db.query(LearningPathStep).filter(LearningPathStep.path_id == active_path.id).all()
        if steps:
            completed = sum(1 for s in steps if s.status == "completed")
            roadmap_completion_pct = round(completed / len(steps), 3)

    return ProgressOverview(
        subject_id=subject_id,
        topics_total=len(topics),
        topics_mastered=topics_mastered,
        overall_accuracy=overall_accuracy,
        total_attempts=total_attempts,
        total_correct=total_correct,
        weak_topic_count=weak_topic_count,
        roadmap_completion_pct=roadmap_completion_pct,
        topic_mastery=topic_mastery,
    )


def get_progress_history(db: Session, user_id: str, subject_id: str, days: int) -> ProgressHistory:
    topic_ids = [row[0] for row in db.query(Topic.id).filter(Topic.subject_id == subject_id).all()]

    since = datetime.utcnow() - timedelta(days=days - 1)
    by_day: dict[str, DailyActivity] = {}
    if topic_ids:
        rows = (
            db.query(
                func.date(QuizAttempt.attempted_at).label("day"),
                func.count(QuizAttempt.id).label("attempts"),
                func.sum(case((QuizAttempt.is_correct == True, 1), else_=0)).label("correct"),  # noqa: E712
            )
            .filter(
                QuizAttempt.user_id == user_id,
                QuizAttempt.topic_id.in_(topic_ids),
                QuizAttempt.attempted_at >= since,
            )
            .group_by(func.date(QuizAttempt.attempted_at))
            .all()
        )
        by_day = {
            str(r.day): DailyActivity(date=str(r.day), attempts=r.attempts, correct=int(r.correct or 0))
            for r in rows
        }

    daily_activity = []
    for i in range(days):
        day_key = str((since + timedelta(days=i)).date())
        daily_activity.append(by_day.get(day_key, DailyActivity(date=day_key, attempts=0, correct=0)))

    return ProgressHistory(subject_id=subject_id, days=days, daily_activity=daily_activity)
