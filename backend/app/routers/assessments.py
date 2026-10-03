import json
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import (
    QuizAttempt,
    QuizQuestion,
    SkillAssessment,
    Subject,
    Topic,
    TopicPrerequisite,
    User,
)
from app.schemas.assessments import (
    AssessmentOut,
    AssessmentQuestionOut,
    AssessmentStartRequest,
    AssessmentStartResponse,
    AssessmentSubmitRequest,
    AssessmentSubmitResponse,
    TopicMasteryResult,
)
from app.services.grading import grade_answer
from app.services.mastery import apply_answer

router = APIRouter(prefix="/api/assessments", tags=["assessments"])

QUESTIONS_PER_TOPIC = 3
MAX_ENTRY_TOPICS = 5


def _entry_topics_for_subject(db: Session, subject_id: str) -> list[Topic]:
    """
    Topics with no prerequisites -- the natural starting point for a
    diagnostic, since a learner shouldn't be tested on something that
    depends on a topic they haven't been placed on yet.
    """
    topics_with_prereqs = {row[0] for row in db.query(TopicPrerequisite.topic_id).distinct()}
    all_topics = db.query(Topic).filter(Topic.subject_id == subject_id).all()
    entry_topics = [t for t in all_topics if t.id not in topics_with_prereqs]
    return entry_topics[:MAX_ENTRY_TOPICS]


@router.post("/start", response_model=AssessmentStartResponse, status_code=201)
def start_assessment(
    payload: AssessmentStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    entry_topics = _entry_topics_for_subject(db, subject.id)
    if not entry_topics:
        raise HTTPException(
            status_code=400,
            detail="This subject has no entry-level topics with quiz questions yet.",
        )

    questions: list[QuizQuestion] = []
    for topic in entry_topics:
        topic_questions = (
            db.query(QuizQuestion)
            .filter(QuizQuestion.topic_id == topic.id)
            .order_by(QuizQuestion.difficulty_level)
            .limit(QUESTIONS_PER_TOPIC)
            .all()
        )
        questions.extend(topic_questions)

    if not questions:
        raise HTTPException(
            status_code=400,
            detail="No quiz questions exist yet for this subject's entry topics.",
        )

    assessment = SkillAssessment(
        user_id=current_user.id,
        subject_id=subject.id,
        status="in_progress",
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    question_out = [
        AssessmentQuestionOut(
            id=q.id,
            topic_id=q.topic_id,
            difficulty_level=q.difficulty_level,
            question_type=q.question_type.value if hasattr(q.question_type, "value") else q.question_type,
            prompt=q.prompt,
            choices=json.loads(q.choices) if q.choices else None,
        )
        for q in questions
    ]

    return AssessmentStartResponse(
        assessment_id=assessment.id,
        subject_id=subject.id,
        questions=question_out,
    )


@router.post("/{assessment_id}/submit", response_model=AssessmentSubmitResponse)
def submit_assessment(
    assessment_id: str,
    payload: AssessmentSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessment = (
        db.query(SkillAssessment)
        .filter(
            and_(
                SkillAssessment.id == assessment_id,
                SkillAssessment.user_id == current_user.id,
            )
        )
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status == "completed":
        raise HTTPException(status_code=400, detail="Assessment already submitted")

    if not payload.answers:
        raise HTTPException(status_code=400, detail="No answers submitted")

    question_ids = [a.question_id for a in payload.answers]
    questions_by_id = {
        q.id: q
        for q in db.query(QuizQuestion).filter(QuizQuestion.id.in_(question_ids)).all()
    }

    # Diagnostic mode: a single answer shouldn't be treated as "teaching" the
    # topic, so p_learn=0 here -- this establishes a baseline, phase 5's
    # practice-mode calls will use the normal p_learn > 0.
    correct_by_topic: dict[str, int] = defaultdict(int)
    total_by_topic: dict[str, int] = defaultdict(int)
    total_correct = 0

    for answer in payload.answers:
        question = questions_by_id.get(answer.question_id)
        if question is None:
            continue  # unknown/stale question id -- skip rather than fail the whole submission

        is_correct = grade_answer(question, answer.user_answer)

        db.add(
            QuizAttempt(
                user_id=current_user.id,
                question_id=question.id,
                topic_id=question.topic_id,
                user_answer=answer.user_answer,
                is_correct=is_correct,
                difficulty_level=question.difficulty_level,
                response_time_seconds=answer.response_time_seconds,
            )
        )

        apply_answer(db, current_user.id, question.topic_id, is_correct, p_learn=0.0)

        total_by_topic[question.topic_id] += 1
        if is_correct:
            correct_by_topic[question.topic_id] += 1
            total_correct += 1

    assessment.status = "completed"
    assessment.completed_at = datetime.utcnow()
    db.commit()

    topic_ids = list(total_by_topic.keys())
    topics_by_id = {t.id: t for t in db.query(Topic).filter(Topic.id.in_(topic_ids)).all()}

    from app.models import MasteryScore  # local import to avoid unused-import lint upstream

    mastery_rows = {
        m.topic_id: m
        for m in db.query(MasteryScore)
        .filter(MasteryScore.user_id == current_user.id, MasteryScore.topic_id.in_(topic_ids))
        .all()
    }

    topic_results = [
        TopicMasteryResult(
            topic_id=topic_id,
            topic_name=topics_by_id[topic_id].name if topic_id in topics_by_id else "unknown",
            correct=correct_by_topic[topic_id],
            total=total_by_topic[topic_id],
            mastery_probability=mastery_rows[topic_id].mastery_probability
            if topic_id in mastery_rows
            else 0.0,
        )
        for topic_id in topic_ids
    ]

    total_answered = sum(total_by_topic.values())
    overall_score = total_correct / total_answered if total_answered else 0.0

    return AssessmentSubmitResponse(
        assessment_id=assessment.id,
        status=assessment.status,
        overall_score=round(overall_score, 3),
        topic_results=topic_results,
    )


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    assessment = (
        db.query(SkillAssessment)
        .filter(
            and_(
                SkillAssessment.id == assessment_id,
                SkillAssessment.user_id == current_user.id,
            )
        )
        .first()
    )
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment
