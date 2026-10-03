"""
Generates new multiple-choice quiz questions for a topic at a given
difficulty level, grounded in the RAG knowledge base (falls back to general
knowledge if nothing's been ingested for the topic, same as study material
generation). Used by the adaptive quiz engine when it runs out of unseen
questions at a learner's target difficulty.
"""

from app.models import QuestionType, QuizQuestion, Topic
from app.services.llm import generate_json
from app.services.rag import retrieve_relevant_chunks
from sqlalchemy.orm import Session
import json

TOP_K_CHUNKS = 5

_DIFFICULTY_LABELS = {
    1: "very easy, testing basic recall",
    2: "easy",
    3: "moderate",
    4: "challenging",
    5: "very challenging, testing deep or edge-case understanding",
}


def _validate_item(item: dict) -> bool:
    required = {"prompt", "choices", "correct_answer"}
    if not required.issubset(item.keys()):
        return False
    if not isinstance(item["choices"], list) or len(item["choices"]) < 2:
        return False
    if item["correct_answer"] not in item["choices"]:
        return False
    return True


def generate_questions_for_topic(
    db: Session, topic_id: str, difficulty_level: int = 1, count: int = 3
) -> list[QuizQuestion]:
    """
    Creates `count` new QuizQuestion rows (is_ai_generated=True) for the
    topic. Does not commit -- caller controls the transaction. Raises on
    LLM/parsing failure; callers in the adaptive quiz flow should catch this
    and fall back to the existing question bank rather than fail the request.
    """
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if topic is None:
        raise ValueError(f"Topic {topic_id} does not exist")

    chunks = retrieve_relevant_chunks(db, topic_id=topic_id, query=topic.name, k=TOP_K_CHUNKS)
    context = "\n\n---\n\n".join(c.content for c in chunks)
    level_label = _DIFFICULTY_LABELS.get(difficulty_level, "moderate")

    system_prompt = (
        "You write multiple-choice quiz questions for a learning app. "
        "Base every question strictly on the provided reference material when it's "
        "non-empty; if it's empty, use well-established general knowledge about the "
        "topic instead and keep questions unambiguous. Each question needs exactly "
        "4 plausible choices with exactly one correct answer, plus a one-sentence "
        "explanation of why it's correct."
    )
    user_prompt = (
        f'Topic: "{topic.name}"\n'
        f"Description: {topic.description or 'none provided'}\n"
        f"Difficulty: {level_label} (level {difficulty_level}/5)\n"
        f"Number of questions: {count}\n\n"
        f"Reference material (may be empty):\n{context or '(none ingested for this topic yet)'}\n\n"
        'Respond with JSON of the shape: {"questions": [{"prompt": str, '
        '"choices": [str, str, str, str], "correct_answer": str, "explanation": str}]}'
    )

    result = generate_json(system_prompt, user_prompt, max_tokens=1800)
    raw_items = result.get("questions", []) if isinstance(result, dict) else []

    created: list[QuizQuestion] = []
    for item in raw_items:
        if not isinstance(item, dict) or not _validate_item(item):
            continue  # skip malformed items rather than fail the whole batch
        question = QuizQuestion(
            topic_id=topic_id,
            difficulty_level=difficulty_level,
            question_type=QuestionType.multiple_choice,
            prompt=item["prompt"],
            choices=_dump_choices(item["choices"]),
            correct_answer=item["correct_answer"],
            explanation=item.get("explanation", ""),
            is_ai_generated=True,
        )
        db.add(question)
        created.append(question)

    return created


def _dump_choices(choices: list[str]) -> str:
    return json.dumps(choices)
