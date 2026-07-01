"""Serviço de autenticação e gestão de usuários."""

from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from app.repositories.pending_registration_repository import PendingRegistrationRepository
from app.services.email_service import EmailService
from app.schemas.user import UserRegister, TokenResponse
from app.security.jwt import create_access_token
from app.security.password import verify_password, get_password_hash
import random


class AuthService:
    """Lógica de negócio de autenticação."""

    def __init__(self, db: Session) -> None:
        self.user_repo = UserRepository(db)
        self.pending_repo = PendingRegistrationRepository(db)

    def register(self, user_data: UserRegister) -> dict:
        """Registra uma solicitação pendente de usuário e envia e-mail."""
        existing = self.user_repo.get_by_email(user_data.email)
        if existing:
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="REGISTER_FAILURE",
                    resource="user",
                    user_email=user_data.email,
                    details=f"Tentativa de cadastro falhou: o e-mail '{user_data.email}' já está cadastrado."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha de cadastro): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este e-mail já está cadastrado.",
            )

        # Gera código de 6 dígitos
        code = str(random.randint(100000, 999999))
        hashed_password = get_password_hash(user_data.password)

        # Salva ou atualiza registro pendente
        self.pending_repo.create_or_update(
            email=user_data.email,
            password_hash=hashed_password,
            code=code,
        )

        # Dispara e-mail via Resend
        email_sent = EmailService.send_verification_email(user_data.email, code)
        if not email_sent:
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="REGISTER_FAILURE",
                    resource="user",
                    user_email=user_data.email,
                    details=f"Tentativa de cadastro para '{user_data.email}' falhou: erro ao enviar e-mail de verificação."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha de cadastro - envio de email): {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao enviar e-mail de verificação. Tente novamente mais tarde.",
            )

        return {
            "message": "Código de verificação enviado para o seu e-mail.",
            "email": user_data.email
        }

    def verify_register(self, email: str, code: str) -> UserModel:
        """Valida o código de verificação e conclui a criação da conta do usuário."""
        # 1. Verifica se já está cadastrado (segurança extra)
        existing = self.user_repo.get_by_email(email)
        if existing:
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="REGISTER_FAILURE",
                    resource="user",
                    user_email=email,
                    details=f"Confirmação de cadastro falhou: o e-mail '{email}' já está ativo no sistema."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha verificação): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este e-mail já está cadastrado.",
            )

        # 2. Busca registro pendente
        pending = self.pending_repo.get_by_email(email)
        if not pending:
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="REGISTER_FAILURE",
                    resource="user",
                    user_email=email,
                    details=f"Confirmação de cadastro falhou: nenhum registro pendente para '{email}'."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha verificação - pendente não encontrado): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhum registro de cadastro pendente encontrado para este e-mail.",
            )

        # 3. Valida código
        if pending.code != code:
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="REGISTER_FAILURE",
                    resource="user",
                    user_email=email,
                    details=f"Confirmação de cadastro falhou: código de verificação incorreto fornecido para '{email}'."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha verificação - código incorreto): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de verificação inválido.",
            )

        # 4. Valida expiração
        from datetime import timezone
        expires_at = pending.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="REGISTER_FAILURE",
                    resource="user",
                    user_email=email,
                    details=f"Confirmação de cadastro falhou: código de verificação expirado para '{email}'."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha verificação - código expirado): {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de verificação expirado. Solicite o cadastro novamente.",
            )

        # 5. Cria usuário definitivo
        user = self.user_repo.create_with_hash(
            email=pending.email,
            hashed_password=pending.hashed_password,
            role="user",
        )

        # 6. Remove registro pendente
        self.pending_repo.delete(pending)

        # 7. Loga na auditoria
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.user_repo.db)
            audit_service.log(
                action="REGISTER",
                resource="user",
                resource_id=str(user.id),
                user_id=user.id,
                user_email=user.email,
                details=f"Cadastro de usuário '{user.email}' verificado e ativado com sucesso."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (cadastro): {e}")

        return user

    def login(self, email: str, password: str) -> dict:
        """Autentica um usuário e retorna o token JWT."""
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            try:
                from app.services.audit_log_service import AuditLogService
                audit_service = AuditLogService(self.user_repo.db)
                audit_service.log(
                    action="LOGIN_FAILURE",
                    resource="user",
                    user_id=user.id if user else None,
                    user_email=email,
                    details=f"Tentativa de login falhou: e-mail ou senha incorretos para '{email}'."
                )
            except Exception as e:
                print(f"Erro ao criar log de auditoria (falha login): {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="E-mail ou senha incorretos.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.banned_until:
            from datetime import datetime, UTC, timezone
            banned_until = user.banned_until
            if banned_until.tzinfo is None:
                banned_until = banned_until.replace(tzinfo=timezone.utc)
            if banned_until > datetime.now(UTC):
                ban_str = banned_until.strftime("%d/%m/%Y %H:%M:%S")
                try:
                    from app.services.audit_log_service import AuditLogService
                    audit_service = AuditLogService(self.user_repo.db)
                    audit_service.log(
                        action="LOGIN_FAILURE",
                        resource="user",
                        resource_id=str(user.id),
                        user_id=user.id,
                        user_email=user.email,
                        details=f"Tentativa de login falhou: conta do usuário '{user.email}' está banida até {ban_str}."
                    )
                except Exception as e:
                    print(f"Erro ao criar log de auditoria (falha login - banido): {e}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Sua conta está temporariamente banida até {ban_str}.",
                )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=access_token_expires,
        )

        # Loga na auditoria
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.user_repo.db)
            audit_service.log(
                action="LOGIN",
                resource="user",
                resource_id=str(user.id),
                user_id=user.id,
                user_email=user.email,
                details=f"Login realizado com sucesso."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (login): {e}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }

    def forgot_password(self, email: str) -> dict:
        """Gera um token de redefinição de senha (mock)."""
        user = self.user_repo.get_by_email(email)
        if not user:
            # Avoid user enumeration, pretend it was sent anyway
            return {"message": "Caso o e-mail exista, um código de redefinição foi gerado."}

        # Generate mock reset token
        reset_token = f"reset-{int(datetime.now(UTC).timestamp())}"
        self.user_repo.set_reset_token(user, reset_token)

        # PRINT IN CONTAINER LOG FOR USER ACCESS
        print("\n" + "=" * 80)
        print(f"MOCK PASSWORD RESET LINK FOR: {user.email}")
        print(f"Use the token: {reset_token}")
        print(f"Redefinition parameters: ?email={user.email}&token={reset_token}")
        print("=" * 80 + "\n")

        # Loga na auditoria
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.user_repo.db)
            audit_service.log(
                action="PASSWORD_FORGOT",
                resource="user",
                resource_id=str(user.id),
                user_id=user.id,
                user_email=user.email,
                details="Solicitação de recuperação de senha gerada."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (recuperação de senha): {e}")

        return {
            "message": "Caso o e-mail exista, um código de redefinição foi gerado. Verifique os logs do Docker para resgatar seu link.",
            "debug_token": reset_token,  # Send directly for UI developer ease
        }

    def reset_password(self, email: str, token: str, new_password: str) -> dict:
        """Redefine a senha do usuário usando o token de reset."""
        user = self.user_repo.get_by_email(email)
        if not user or user.reset_token != token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token de redefinição inválido ou e-mail inválido.",
            )

        self.user_repo.update_password(user, new_password)

        # Loga na auditoria
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.user_repo.db)
            audit_service.log(
                action="PASSWORD_RESET",
                resource="user",
                resource_id=str(user.id),
                user_id=user.id,
                user_email=user.email,
                details="Senha alterada/redefinida com sucesso utilizando token."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (redefinição de senha): {e}")

        return {"message": "Senha redefinida com sucesso."}

    def logout(self, user: UserModel) -> dict:
        """Registra o logout do usuário na auditoria."""
        try:
            from app.services.audit_log_service import AuditLogService
            audit_service = AuditLogService(self.user_repo.db)
            audit_service.log(
                action="LOGOUT",
                resource="user",
                resource_id=str(user.id),
                user_id=user.id,
                user_email=user.email,
                details=f"Logout realizado com sucesso pelo usuário '{user.email}'."
            )
        except Exception as e:
            print(f"Erro ao criar log de auditoria (logout): {e}")

        return {"message": "Logout registrado com sucesso."}
