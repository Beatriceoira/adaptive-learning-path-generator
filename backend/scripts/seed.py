"""
Seed the database with a small sample subject + topic graph so the API is
testable end-to-end before the LLM/RAG generation (phase 4) exists.

Run with:  python -m scripts.seed
"""

import json

from app.database import Base, SessionLocal, engine, ensure_pgvector_extension
from app.models import QuizQuestion, Subject, Topic, TopicPrerequisite


def _q(topic_id, difficulty, prompt, choices, correct_answer, explanation=""):
    return QuizQuestion(
        topic_id=topic_id,
        difficulty_level=difficulty,
        question_type="multiple_choice",
        prompt=prompt,
        choices=json.dumps(choices),
        correct_answer=correct_answer,
        explanation=explanation,
        is_ai_generated=False,
    )


def run():
    ensure_pgvector_extension()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Subject).filter(Subject.name == "Python Programming").first():
            print("Sample data already seeded, skipping.")
            return

        subject = Subject(
            name="Python Programming",
            description="Core Python from fundamentals to intermediate topics.",
        )
        db.add(subject)
        db.flush()

        variables = Topic(subject_id=subject.id, name="Variables & Data Types", difficulty_level=1)
        control_flow = Topic(subject_id=subject.id, name="Control Flow (if/for/while)", difficulty_level=1)
        functions = Topic(subject_id=subject.id, name="Functions", difficulty_level=2)
        oop = Topic(subject_id=subject.id, name="Object-Oriented Programming", difficulty_level=3)
        decorators = Topic(subject_id=subject.id, name="Decorators & Closures", difficulty_level=4)

        db.add_all([variables, control_flow, functions, oop, decorators])
        db.flush()

        db.add_all(
            [
                TopicPrerequisite(topic_id=control_flow.id, prerequisite_id=variables.id),
                TopicPrerequisite(topic_id=functions.id, prerequisite_id=control_flow.id),
                TopicPrerequisite(topic_id=oop.id, prerequisite_id=functions.id),
                TopicPrerequisite(topic_id=decorators.id, prerequisite_id=functions.id),
            ]
        )

        # Sample quiz questions for the first two topics, spanning difficulty 1-3.
        # Note: only `variables` is an *entry* topic (no prerequisites), and the
        # diagnostic only samples entry topics, so the diagnostic draws its
        # questions from `variables`; the control-flow questions are served by
        # the adaptive quiz. Phases 4/5 extend this with AI-generated,
        # RAG-grounded questions.
        db.add_all(
            [
                _q(variables.id, 1, "What does `type(3.0)` return in Python?",
                   ["int", "float", "str", "complex"], "float"),
                _q(variables.id, 2, "Which of these is immutable in Python?",
                   ["list", "dict", "tuple", "set"], "tuple"),
                _q(variables.id, 3, "What is the result of `5 // 2` in Python?",
                   ["2.5", "2", "3", "2.0"], "2"),
                _q(control_flow.id, 1, "Which keyword starts a loop that repeats while a condition holds?",
                   ["for", "while", "loop", "repeat"], "while"),
                _q(control_flow.id, 2, "What does `break` do inside a loop?",
                   ["Skips to the next iteration", "Exits the loop entirely",
                    "Restarts the loop", "Raises an exception"], "Exits the loop entirely"),
                _q(control_flow.id, 3, "What does `range(1, 10, 2)` produce?",
                   ["1,2,3,...,10", "1,3,5,7,9", "2,4,6,8,10", "1,10"], "1,3,5,7,9"),
            ]
        )

        db.commit()
        print(f"Seeded subject '{subject.name}' with 5 topics and 6 sample quiz questions.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
