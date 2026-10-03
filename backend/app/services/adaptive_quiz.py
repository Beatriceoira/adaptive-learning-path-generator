"""
The adaptive layer: picks which difficulty level a learner should be quizzed
at right now (from their current BKT mastery estimate) and finds an
appropriate unseen question, generating fresh ones via the LLM if the
existing bank has run dry at that level.

Deliberately stateless between calls -- there's no "quiz session" row.
Each call reads the learner's current `mastery_scores` row and their
`quiz_attempts` history for the topic, so "next question" always reflects
the very latest evidence, including the answer they just submitted.
"""

import logging

from sqlalchemy.orm import Session

from app.models import QuizAttempt, QuizQuestion
from app.services.mastery import get_or_create_mastery
from app.services.quiz_generation import generate_questions_for_topic

logger = logging.getLogger(__name__)

MIN_DIFFICULTY = 1
MAX_DIFFICULTY = 5
GENERATE_BATCH_SIZE = 3

# Ordered low->high; a learner below each upper bound is placed at that level.
_MASTERY_BREAKPOINTS = [(0.3, 1), (0.5, 2), (0.7, 3), (0.85, 4)]


def difficulty_from_mastery(mastery_probability: float) -> int:
    for upper_bound, level in _MASTERY_BREAKPOINTS:
        if mastery_probability < upper_bound:
            return level
    return 5


def _difficulty_search_order(target: int) -> list[int]:
    """Target first, then alternating outward (target-1, target+1, target-2, ...), clamped to 1-5."""
    order = [target]
    offset = 1
    while len(order) < (MAX_DIFFICULTY - MIN_DIFFICULTY + 1):
        for candidate in (target - offset, target + offset):
            if MIN_DIFFICULTY <= candidate <= MAX_DIFFICULTY and candidate not in order:
                order.append(candidate)
        offset += 1
    return order


def _attempted_question_ids(db: Session, user_id: str, topic_id: str) -> set[str]:
    rows = (
        db.query(QuizAttempt.question_id)
        .filter(QuizAttempt.user_id == user_id, QuizAttempt.topic_id == topic_id)
        .all()
    )
    return {r[0] for r in rows}


def _find_unseen(db: Session, topic_id: str, difficulty: int, excluded_ids: set[str]) -> QuizQuestion | None:
    query = db.query(QuizQuestion).filter(
        QuizQuestion.topic_id == topic_id, QuizQuestion.difficulty_level == difficulty
    )
    if excluded_ids:
        query = query.filter(~QuizQuestion.id.in_(excluded_ids))
    return query.first()


def get_next_question(db: Session, user_id: str, topic_id: str) -> tuple[QuizQuestion, int, bool]:
    """
    Returns (question, target_difficulty, was_freshly_generated).
    Raises ValueError only if the topic has no questions at all and AI
    generation is unavailable/fails -- everything else degrades gracefully.
    """
    mastery = get_or_create_mastery(db, user_id, topic_id)
    db.commit()  # persist a freshly-created mastery row before we read it again below
    target = difficulty_from_mastery(mastery.mastery_probability)
    excluded_ids = _attempted_question_ids(db, user_id, topic_id)

    # 1) Unseen question, searching outward from the target difficulty.
    for level in _difficulty_search_order(target):
        question = _find_unseen(db, topic_id, level, excluded_ids)
        if question:
            return question, target, False

    # 2) Nothing unseen anywhere for this topic -- try generating fresh ones at the target level.
    try:
        new_questions = generate_questions_for_topic(db, topic_id, target, count=GENERATE_BATCH_SIZE)
        if new_questions:
            db.commit()
            return new_questions[0], target, True
    except Exception:
        logger.warning("AI quiz generation failed for topic %s; falling back to repeats", topic_id, exc_info=True)
        db.rollback()

    # 3) Last resort: repeat a previously-seen question at the target difficulty (or any difficulty).
    fallback = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.topic_id == topic_id, QuizQuestion.difficulty_level == target)
        .first()
        or db.query(QuizQuestion).filter(QuizQuestion.topic_id == topic_id).first()
    )
    if fallback:
        return fallback, target, False

    raise ValueError("No quiz questions exist for this topic yet, and AI generation is unavailable.")
