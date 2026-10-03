from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.study_material import StudyMaterialGenerateRequest, StudyMaterialOut
from app.services.study_material import generate_study_material, get_cached_material

router = APIRouter(prefix="/api/study-material", tags=["study-material"])


@router.post("/generate", response_model=StudyMaterialOut, status_code=201)
def generate(
    payload: StudyMaterialGenerateRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    try:
        material = generate_study_material(
            db, payload.topic_id, payload.difficulty_level, payload.force_regenerate
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM generation failed: {e}")

    return material


@router.get("/{topic_id}", response_model=StudyMaterialOut)
def get_material(
    topic_id: str,
    difficulty_level: int = 1,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    material = get_cached_material(db, topic_id, difficulty_level)
    if not material:
        raise HTTPException(
            status_code=404,
            detail="No study material generated yet for this topic/difficulty. POST to /generate first.",
        )
    return material
