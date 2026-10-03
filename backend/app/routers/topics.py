from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Subject, Topic, TopicPrerequisite, User
from app.schemas.topics import SubjectCreate, SubjectOut, TopicCreate, TopicOut

router = APIRouter(prefix="/api", tags=["topics"])


@router.post("/subjects", response_model=SubjectOut, status_code=201)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    subject = Subject(name=payload.name, description=payload.description)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db)):
    return db.query(Subject).all()


@router.post("/topics", response_model=TopicOut, status_code=201)
def create_topic(
    payload: TopicCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    topic = Topic(
        subject_id=payload.subject_id,
        name=payload.name,
        description=payload.description,
        difficulty_level=payload.difficulty_level,
    )
    db.add(topic)
    db.flush()  # get topic.id before committing

    for prereq_id in payload.prerequisite_ids:
        db.add(TopicPrerequisite(topic_id=topic.id, prerequisite_id=prereq_id))

    db.commit()
    db.refresh(topic)
    return topic


@router.get("/subjects/{subject_id}/topics", response_model=list[TopicOut])
def list_topics_for_subject(subject_id: str, db: Session = Depends(get_db)):
    return db.query(Topic).filter(Topic.subject_id == subject_id).all()


@router.get("/topics/{topic_id}", response_model=TopicOut)
def get_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
