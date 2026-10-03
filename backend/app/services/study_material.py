"""
Generates (and caches) AI study material for a topic at a given difficulty
level, grounded in whatever's been ingested into the RAG knowledge base for
that topic. Cache key is (topic_id, difficulty_level) -- see StudyMaterial
in the schema; regenerating is opt-in via force_regenerate.
"""

import json

from sqlalchemy.orm import Session

from app.models import StudyMaterial, Topic
from app.services.llm import generate_text
from app.services.rag import retrieve_relevant_chunks

TOP_K_CHUNKS = 6

_DIFFICULTY_LABELS = {
    1: "complete beginner, assume no prior knowledge",
    2: "beginner, comfortable with the basics of the subject",
    3: "intermediate",
    4: "advanced",
    5: "expert / preparing for mastery-level questions",
}


def get_cached_material(db: Session, topic_id: str, difficulty_level: int) -> StudyMaterial | None:
    return (
        db.query(StudyMaterial)
        .filter(StudyMaterial.topic_id == topic_id, StudyMaterial.difficulty_level == difficulty_level)
        .order_by(StudyMaterial.generated_at.desc())
        .first()
    )


def generate_study_material(
    db: Session, topic_id: str, difficulty_level: int = 1, force_regenerate: bool = False
) -> StudyMaterial:
    if not force_regenerate:
        cached = get_cached_material(db, topic_id, difficulty_level)
        if cached:
            return cached

    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        raise ValueError(f"Topic {topic_id} does not exist")

    chunks = retrieve_relevant_chunks(db, topic_id=topic_id, query=topic.name, k=TOP_K_CHUNKS)
    grounded = bool(chunks)
    context = "\n\n---\n\n".join(c.content for c in chunks)

    level_label = _DIFFICULTY_LABELS.get(difficulty_level, "intermediate")
    system_prompt = (
        "You are a patient, clear tutor writing study material in Markdown. "
        "Write for a learner who is " + level_label + ". "
        "Use headings, short paragraphs, and at least one concrete example. "
        "Base every factual claim strictly on the provided reference material -- "
        "if reference material is empty, say so isn't available and teach from "
        "well-established general knowledge instead, staying conservative about claims."
    )
    user_prompt = (
        f"Topic: {topic.name}\n"
        f"Topic description: {topic.description or 'none provided'}\n\n"
        f"Reference material (grounded={grounded}):\n{context or '(none ingested yet for this topic)'}"
    )

    content_markdown = generate_text(system_prompt, user_prompt, max_tokens=1500)

    material = StudyMaterial(
        topic_id=topic_id,
        difficulty_level=difficulty_level,
        content_markdown=content_markdown,
        source_chunks=json.dumps([c.id for c in chunks]),
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material
