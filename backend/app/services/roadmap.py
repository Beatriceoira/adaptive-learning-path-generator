"""
Generates a personalized learning path for a user in a subject:

1. Topologically sorts the subject's topics by their prerequisite graph
   (a topic never appears before something it depends on).
2. Marks any topic the user has already sufficiently mastered (from
   phase 3's diagnostic, or later quiz attempts) as `completed` up front,
   so the roadmap doesn't waste their time re-teaching what they know.
3. Asks the LLM for a short, human-readable rationale for the path,
   grounded in a handful of retrieved knowledge chunks so it can reference
   real content rather than generic filler -- falls back to a template
   sentence if nothing has been ingested yet for this subject, or if the
   LLM/embedding call fails for any reason.
"""

from collections import defaultdict, deque

from sqlalchemy.orm import Session

from app.models import (
    LearningPath,
    LearningPathStep,
    MasteryScore,
    Topic,
    TopicPrerequisite,
)
from app.services.llm import generate_text
from app.services.rag import retrieve_relevant_chunks

MASTERY_THRESHOLD = 0.7  # P(mastery) at/above this -> step starts pre-marked "completed"


def _topological_order(topics: list[Topic], prereq_edges: list[TopicPrerequisite]) -> list[Topic]:
    """Kahn's algorithm. Ties (topics with equal in-degree) break by difficulty_level, then name."""
    topics_by_id = {t.id: t for t in topics}
    in_degree = {t.id: 0 for t in topics}
    dependents = defaultdict(list)  # prerequisite_id -> [topic_ids that depend on it]

    for edge in prereq_edges:
        if edge.topic_id not in in_degree or edge.prerequisite_id not in in_degree:
            continue  # prerequisite outside this subject's topic set -- ignore rather than fail
        in_degree[edge.topic_id] += 1
        dependents[edge.prerequisite_id].append(edge.topic_id)

    ready = deque(
        sorted(
            (tid for tid, deg in in_degree.items() if deg == 0),
            key=lambda tid: (topics_by_id[tid].difficulty_level, topics_by_id[tid].name),
        )
    )
    ordered: list[Topic] = []

    while ready:
        current_id = ready.popleft()
        ordered.append(topics_by_id[current_id])
        newly_ready = []
        for dependent_id in dependents[current_id]:
            in_degree[dependent_id] -= 1
            if in_degree[dependent_id] == 0:
                newly_ready.append(dependent_id)
        for tid in sorted(newly_ready, key=lambda tid: (topics_by_id[tid].difficulty_level, topics_by_id[tid].name)):
            ready.append(tid)

    if len(ordered) < len(topics):
        # Cycle in the prerequisite graph -- append whatever's left in a stable order
        # rather than silently dropping topics from the roadmap.
        remaining = [t for t in topics if t.id not in {o.id for o in ordered}]
        ordered.extend(sorted(remaining, key=lambda t: (t.difficulty_level, t.name)))

    return ordered


def _build_rationale(
    db: Session, subject_name: str, ordered_topics: list[Topic], weak_topic_names: list[str]
) -> str:
    # Ground the rationale in real content for the first topic, if any has been ingested.
    context = ""
    if ordered_topics:
        chunks = retrieve_relevant_chunks(db=db, topic_id=ordered_topics[0].id, query=ordered_topics[0].name, k=3)
        if chunks:
            context = "\n\n".join(c.content for c in chunks)

    topic_list = ", ".join(t.name for t in ordered_topics)
    weak_note = (
        f"The learner tested weakest on: {', '.join(weak_topic_names)}. Prioritize extra encouragement there."
        if weak_topic_names
        else "No particular weak spots were flagged yet."
    )

    system_prompt = (
        "You are an encouraging, concise learning coach. Write a 3-4 sentence "
        "overview of a learner's personalized study roadmap. Reference the actual "
        "topic order given. Do not invent facts not supported by the provided context. "
        "If context is empty, speak generally about the topic order instead."
    )
    user_prompt = (
        f"Subject: {subject_name}\n"
        f"Topic order: {topic_list}\n"
        f"{weak_note}\n\n"
        f"Reference context (may be empty):\n{context}"
    )

    try:
        return generate_text(system_prompt, user_prompt, max_tokens=250)
    except Exception:
        # LLM/embedding call failed (no API key, network, etc.) -- the roadmap
        # itself is still valid without a rationale, so degrade gracefully.
        return (
            f"Your path through {subject_name} covers {len(ordered_topics)} topics, "
            f"starting with {ordered_topics[0].name if ordered_topics else 'the basics'} "
            "and building up in prerequisite order."
        )


def generate_roadmap(db: Session, user_id: str, subject_id: str) -> LearningPath:
    topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()
    if not topics:
        raise ValueError("Subject has no topics yet")

    prereq_edges = (
        db.query(TopicPrerequisite)
        .filter(TopicPrerequisite.topic_id.in_([t.id for t in topics]))
        .all()
    )
    ordered_topics = _topological_order(topics, prereq_edges)

    mastery_by_topic = {
        m.topic_id: m
        for m in db.query(MasteryScore)
        .filter(MasteryScore.user_id == user_id, MasteryScore.topic_id.in_([t.id for t in topics]))
        .all()
    }
    weak_topic_names = [
        t.name
        for t in ordered_topics
        if mastery_by_topic.get(t.id) and mastery_by_topic[t.id].is_weak_topic
    ]

    # Only one active path per (user, subject) at a time.
    db.query(LearningPath).filter(
        LearningPath.user_id == user_id,
        LearningPath.subject_id == subject_id,
        LearningPath.is_active == True,  # noqa: E712
    ).update({"is_active": False})

    subject_name = topics[0].subject.name if topics[0].subject else "this subject"
    rationale = _build_rationale(db, subject_name, ordered_topics, weak_topic_names)

    path = LearningPath(user_id=user_id, subject_id=subject_id, is_active=True, rationale=rationale)
    db.add(path)
    db.flush()

    for i, topic in enumerate(ordered_topics):
        mastery = mastery_by_topic.get(topic.id)
        status = "completed" if mastery and mastery.mastery_probability >= MASTERY_THRESHOLD else "not_started"
        db.add(
            LearningPathStep(
                path_id=path.id,
                topic_id=topic.id,
                sequence_order=i,
                status=status,
            )
        )

    db.commit()
    db.refresh(path)
    return path
