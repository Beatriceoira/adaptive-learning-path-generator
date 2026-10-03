from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Subject, User
from app.schemas.recommendations import RecommendationsOut
from app.services.recommendations import build_recommendations

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("/{subject_id}", response_model=RecommendationsOut)
def get_recommendations(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    result = build_recommendations(db, current_user.id, subject_id, subject.name)
    return RecommendationsOut(subject_id=subject_id, **result)
