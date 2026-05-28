"""Router de ocorrências — /api/ocorrencias/*"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import UserModel
from app.schemas.ocorrencia import OcorrenciaCreate, OcorrenciaResponse, OcorrenciaStatusUpdate
from app.security.dependencies import get_current_user
from app.services.ocorrencia_service import OcorrenciaService

router = APIRouter(prefix="/api/ocorrencias", tags=["ocorrencias"])


@router.get("", response_model=List[OcorrenciaResponse])
def list_ocorrencias(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    service = OcorrenciaService(db)
    return service.list_ocorrencias(category=category, status_filter=status)


@router.post("", response_model=OcorrenciaResponse, status_code=status.HTTP_201_CREATED)
def create_ocorrencia(
    ocorrencia: OcorrenciaCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = OcorrenciaService(db)
    return service.create_ocorrencia(ocorrencia=ocorrencia, current_user=current_user)


@router.patch("/{ocorrencia_id}/status", response_model=OcorrenciaResponse)
def update_ocorrencia_status(
    ocorrencia_id: int,
    status_update: OcorrenciaStatusUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = OcorrenciaService(db)
    return service.update_status(
        ocorrencia_id=ocorrencia_id,
        status_update=status_update,
        current_user=current_user,
    )


@router.delete("/{ocorrencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ocorrencia(
    ocorrencia_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = OcorrenciaService(db)
    service.delete_ocorrencia(ocorrencia_id=ocorrencia_id, current_user=current_user)
    return None
