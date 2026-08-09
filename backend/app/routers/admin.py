"""Router administrativo — /api/admin/*"""

from typing import List

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import UserModel
from app.schemas.feature_toggle import ToggleResponse
from app.schemas.user import UserResponse, BanUserRequest
from app.schemas.audit_log import AuditLogResponse
from app.security.dependencies import get_current_admin
from app.services.admin_service import AdminService
from app.services.audit_log_service import AuditLogService

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
    return service.update_toggle(key=key, value=value, admin_user=current_user)


@router.post("/batch-resolve")
def batch_resolve_occurrences(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.batch_resolve(admin_user=current_user)


@router.get("/users", response_model=List[UserResponse])
def list_users(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.list_users()


@router.post("/users/{user_id}/ban", response_model=UserResponse)
def ban_user(
    user_id: int,
    req: BanUserRequest,
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    return service.ban_user(user_id=user_id, duration_minutes=req.duration_minutes, admin_user=current_user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AdminService(db)
    service.delete_user(user_id=user_id, admin_user=current_user)
    return None


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    service = AuditLogService(db)
    return service.list_logs()
