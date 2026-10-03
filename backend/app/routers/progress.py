from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Subject, User
from app.schemas.progress import ProgressHistory, ProgressOverview
from app.services.progress import get_progress_history, get_progress_overview

router = APIRouter(prefix="/api/progress", tags=["progress"])

MIN_DAYS = 1
MAX_DAYS = 90
DEFAULT_DAYS = 30


@router.get("/{subject_id}", response_model=ProgressOverview)
def get_overview(
    subject_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return get_progress_overview(db, current_user.id, subject_id)


@router.get("/{subject_id}/history", response_model=ProgressHistory)
def get_history(
    subject_id: str,
    days: int = DEFAULT_DAYS,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    clamped_days = max(MIN_DAYS, min(days, MAX_DAYS))
    return get_progress_history(db, current_user.id, subject_id, clamped_days)
