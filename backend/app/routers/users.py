from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.models import User
from app.schemas.auth import UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
