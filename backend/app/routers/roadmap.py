from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import LearningPath, Subject, Topic, User
from app.schemas.roadmap import RoadmapGenerateRequest, RoadmapOut, RoadmapStepOut
from app.services.roadmap import generate_roadmap

router = APIRouter(prefix="/api/roadmap", tags=["roadmap"])


def _to_roadmap_out(path: LearningPath, db: Session) -> RoadmapOut:
    topic_names = {t.id: t.name for t in db.query(Topic).filter(
        Topic.id.in_([s.topic_id for s in path.steps])
    ).all()}
    return RoadmapOut(
        id=path.id,
        subject_id=path.subject_id,
        created_at=path.created_at,
        is_active=path.is_active,
        rationale=path.rationale,
        steps=[
            RoadmapStepOut(
                topic_id=s.topic_id,
                topic_name=topic_names.get(s.topic_id, "unknown"),
                sequence_order=s.sequence_order,
                status=s.status,
            )
            for s in path.steps
        ],
    )


@router.post("/generate", response_model=RoadmapOut, status_code=201)
def generate(
    payload: RoadmapGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    try:
        path = generate_roadmap(db, current_user.id, payload.subject_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _to_roadmap_out(path, db)


@router.get("/active/{subject_id}", response_model=RoadmapOut)
def get_active_roadmap(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    path = (
        db.query(LearningPath)
        .filter(
            LearningPath.user_id == current_user.id,
            LearningPath.subject_id == subject_id,
            LearningPath.is_active == True,  # noqa: E712
        )
        .first()
    )
    if not path:
        raise HTTPException(status_code=404, detail="No active roadmap for this subject yet")
    return _to_roadmap_out(path, db)
