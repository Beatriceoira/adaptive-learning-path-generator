import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import QuizAttempt, QuizQuestion, Topic, User
from app.schemas.quiz import (
    QuizNextRequest,
    QuizNextResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)
from app.services.adaptive_quiz import difficulty_from_mastery, get_next_question
from app.services.grading import grade_answer
from app.services.mastery import apply_answer

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# Practice-mode learning rate for BKT -- unlike the diagnostic (p_learn=0),
# answering practice questions is itself part of how the learner improves.
PRACTICE_P_LEARN = 0.15


@router.post("/next", response_model=QuizNextResponse)
def next_question(
    payload: QuizNextRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    topic = db.query(Topic).filter(Topic.id == payload.topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    try:
        question, target_difficulty, freshly_generated = get_next_question(
            db, current_user.id, payload.topic_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return QuizNextResponse(
        question_id=question.id,
        topic_id=question.topic_id,
        difficulty_level=question.difficulty_level,
        question_type=question.question_type.value
        if hasattr(question.question_type, "value")
        else question.question_type,
        prompt=question.prompt,
        choices=json.loads(question.choices) if question.choices else None,
        freshly_generated=freshly_generated,
    )


@router.post("/submit", response_model=QuizSubmitResponse)
def submit_answer(
    payload: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    question = db.query(QuizQuestion).filter(QuizQuestion.id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = grade_answer(question, payload.user_answer)

    db.add(
        QuizAttempt(
            user_id=current_user.id,
            question_id=question.id,
            topic_id=question.topic_id,
            user_answer=payload.user_answer,
            is_correct=is_correct,
            difficulty_level=question.difficulty_level,
            response_time_seconds=payload.response_time_seconds,
        )
    )

    mastery = apply_answer(
        db, current_user.id, question.topic_id, is_correct, p_learn=PRACTICE_P_LEARN
    )
    db.commit()
    db.refresh(mastery)

    return QuizSubmitResponse(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=question.explanation,
        mastery_probability=mastery.mastery_probability,
        attempts_count=mastery.attempts_count,
        correct_count=mastery.correct_count,
        next_difficulty_level=difficulty_from_mastery(mastery.mastery_probability),
    )
