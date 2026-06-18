"""Router de ocorrências — /api/ocorrencias/*"""

from typing import List, Optional

from fastapi import APIRouter, Depends, status, File, UploadFile
import uuid
import os
from sqlalchemy.orm import Session


from app.database.session import get_db
from app.models.user import UserModel
from app.schemas.ocorrencia import OcorrenciaCreate, OcorrenciaResponse, OcorrenciaStatusUpdate
from app.security.dependencies import get_current_user, get_current_user_optional
from app.services.ocorrencia_service import OcorrenciaService

router = APIRouter(prefix="/api/ocorrencias", tags=["ocorrencias"])


@router.get("", response_model=List[OcorrenciaResponse])
def list_ocorrencias(
    category: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    service = OcorrenciaService(db)
    return service.list_ocorrencias(category=category, status_filter=status, current_user=current_user)



@router.post("", response_model=OcorrenciaResponse, status_code=status.HTTP_201_CREATED)
def create_ocorrencia(
    ocorrencia: OcorrenciaCreate,
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
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


@router.post("/upload")
async def upload_photo(
    file: UploadFile = File(...),
    current_user: Optional[UserModel] = Depends(get_current_user_optional),
):
    """Realiza o upload de uma foto de ocorrência para o S3/MinIO."""
    if not file.content_type.startswith("image/"):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo enviado deve ser uma imagem.",
        )
        
    file_ext = os.path.splitext(file.filename)[1]
    if not file_ext:
        if file.content_type == "image/jpeg":
            file_ext = ".jpg"
        elif file.content_type == "image/png":
            file_ext = ".png"
        elif file.content_type == "image/gif":
            file_ext = ".gif"
        elif file.content_type == "image/webp":
            file_ext = ".webp"
        else:
            file_ext = ".jpg"
            
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    
    try:
        from app.services.storage_service import upload_file_to_s3
        content = await file.read()
        public_url = upload_file_to_s3(
            file_content=content,
            file_name=unique_filename,
            content_type=file.content_type
        )
        return {"url": public_url}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao realizar upload para o Object Storage: {str(e)}"
        )


@router.post("/{ocorrencia_id}/toggle-afetado", response_model=OcorrenciaResponse)
def toggle_afetado(
    ocorrencia_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = OcorrenciaService(db)
    return service.toggle_afetado(ocorrencia_id=ocorrencia_id, current_user=current_user)


