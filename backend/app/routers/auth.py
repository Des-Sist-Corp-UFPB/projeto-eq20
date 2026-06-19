"""Router de autenticação — /api/auth/*"""

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import UserModel
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserRegister,
    UserResponse,
    UserVerifyRegister,
)
from app.security.dependencies import get_current_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(user)


@router.post("/verify-register", response_model=UserResponse)
def verify_register_user(req: UserVerifyRegister, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.verify_register(email=req.email, code=req.code)


@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    return service.login(email=form_data.username, password=form_data.password)


@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.forgot_password(email=req.email)


@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.reset_password(
        email=req.email,
        token=req.token,
        new_password=req.new_password,
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: UserModel = Depends(get_current_user)):
    return current_user
