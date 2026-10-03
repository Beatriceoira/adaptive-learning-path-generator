"""
Turns a learner's weak-topic flags and active roadmap progress into a
"what should I do next" recommendation: which topics need remediation,
what's up next in the roadmap, and a short LLM-written note tying the two
together (falls back to a template sentence if the LLM call fails, same
pattern as roadmap rationale / study material generation).
"""

from sqlalchemy.orm import Session

from app.models import LearningPath, LearningPathStep, MasteryScore, Topic
from app.services.adaptive_quiz import difficulty_from_mastery
from app.services.llm import generate_text

NEXT_UP_LIMIT = 3


def get_weak_topics(db: Session, user_id: str, subject_id: str) -> list[tuple[MasteryScore, Topic]]:
    topic_ids = [row[0] for row in db.query(Topic.id).filter(Topic.subject_id == subject_id).all()]
    if not topic_ids:
        return []
    return (
        db.query(MasteryScore, Topic)
        .join(Topic, MasteryScore.topic_id == Topic.id)
        .filter(
            MasteryScore.user_id == user_id,
            MasteryScore.topic_id.in_(topic_ids),
            MasteryScore.is_weak_topic == True,  # noqa: E712
        )
        .all()
    )


def get_next_up(db: Session, user_id: str, subject_id: str) -> list[tuple[LearningPathStep, Topic]]:
    path = (
        db.query(LearningPath)
        .filter(
            LearningPath.user_id == user_id,
            LearningPath.subject_id == subject_id,
            LearningPath.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not path:
        return []  # no roadmap generated yet -- not an error, just nothing to recommend from
    return (
        db.query(LearningPathStep, Topic)
        .join(Topic, LearningPathStep.topic_id == Topic.id)
        .filter(LearningPathStep.path_id == path.id, LearningPathStep.status == "not_started")
        .order_by(LearningPathStep.sequence_order)
        .limit(NEXT_UP_LIMIT)
        .all()
    )


def _build_message(subject_name: str, weak_topic_names: list[str], next_up_names: list[str]) -> str:
    if not weak_topic_names and not next_up_names:
        return (
            "Not enough activity yet to personalize recommendations -- take the "
            f"diagnostic or start practicing in {subject_name} to get tailored guidance."
        )

    system_prompt = (
        "You are an encouraging, concise learning coach. Write 2-3 sentences of "
        "personalized, actionable next-step guidance for a learner. Reference only "
        "the topics named below -- do not invent others."
    )
    user_prompt = (
        f"Subject: {subject_name}\n"
        f"Topics they're struggling with: {', '.join(weak_topic_names) or 'none flagged yet'}\n"
        "Next topics up in their roadmap: "
        f"{', '.join(next_up_names) or 'none (no active roadmap, or roadmap complete)'}"
    )
    try:
        return generate_text(system_prompt, user_prompt, max_tokens=200)
    except Exception:
        # LLM call failed (no API key, network, etc.) -- degrade to a plain,
        # still-useful templated message rather than erroring the request.
        parts = []
        if weak_topic_names:
            parts.append(f"Consider reviewing: {', '.join(weak_topic_names)}.")
        if next_up_names:
            parts.append(f"Next up in your roadmap: {', '.join(next_up_names)}.")
        return " ".join(parts) or "Keep going!"


def build_recommendations(db: Session, user_id: str, subject_id: str, subject_name: str) -> dict:
    weak = get_weak_topics(db, user_id, subject_id)
    next_up = get_next_up(db, user_id, subject_id)

    weak_topics_out = [
        {
            "topic_id": topic.id,
            "topic_name": topic.name,
            "mastery_probability": mastery.mastery_probability,
            "attempts_count": mastery.attempts_count,
            "recommended_difficulty": difficulty_from_mastery(mastery.mastery_probability),
        }
        for mastery, topic in weak
    ]
    next_up_out = [
        {"topic_id": topic.id, "topic_name": topic.name, "sequence_order": step.sequence_order}
        for step, topic in next_up
    ]

    message = _build_message(
        subject_name,
        [w["topic_name"] for w in weak_topics_out],
        [n["topic_name"] for n in next_up_out],
    )

    return {"weak_topics": weak_topics_out, "next_up": next_up_out, "message": message}
