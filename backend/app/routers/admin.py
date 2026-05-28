"""Router administrativo — /api/admin/*"""

from typing import List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import UserModel
from app.schemas.feature_toggle import ToggleResponse
from app.schemas.user import UserResponse
from app.security.dependencies import get_current_admin
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/toggles", response_model=List[ToggleResponse])
def get_toggles(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.get_toggles()


@router.post("/toggles", response_model=ToggleResponse)
def update_toggle(
    key: str = Body(..., embed=True),
    value: bool = Body(..., embed=True),
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.update_toggle(key=key, value=value)


@router.post("/batch-resolve")
def batch_resolve_occurrences(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.batch_resolve()


@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.list_users()
