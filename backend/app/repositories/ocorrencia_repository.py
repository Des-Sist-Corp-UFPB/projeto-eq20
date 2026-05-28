"""Repositório de acesso a dados de ocorrências."""

from datetime import datetime, UTC
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ocorrencia import OcorrenciaModel


class OcorrenciaRepository:
    """Operações de banco de dados para a entidade Ocorrência."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        exclude_category: Optional[str] = None,
    ) -> list[OcorrenciaModel]:
        """Lista ocorrências com filtros opcionais."""
        query = self.db.query(OcorrenciaModel)

        if category:
            query = query.filter(OcorrenciaModel.category == category)
        if status:
            query = query.filter(OcorrenciaModel.status == status)
        if exclude_category:
            query = query.filter(OcorrenciaModel.category != exclude_category)

        return query.order_by(OcorrenciaModel.date.desc()).all()

    def get_by_id(self, ocorrencia_id: int) -> Optional[OcorrenciaModel]:
        """Busca uma ocorrência pelo ID."""
        return self.db.query(OcorrenciaModel).filter(OcorrenciaModel.id == ocorrencia_id).first()

    def create(
        self,
        title: str,
        category: str,
        description: str,
        lat: float,
        lng: float,
        type: str,
        user_id: int,
        photo: Optional[str] = None,
    ) -> OcorrenciaModel:
        """Cria uma nova ocorrência no banco."""
        ocorrencia = OcorrenciaModel(
            title=title,
            category=category,
            description=description,
            lat=lat,
            lng=lng,
            photo=photo,
            type=type,
            status="pendente",
            user_id=user_id,
            date=datetime.now(UTC),
        )
        self.db.add(ocorrencia)
        self.db.commit()
        self.db.refresh(ocorrencia)
        return ocorrencia

    def update_status(self, ocorrencia: OcorrenciaModel, new_status: str) -> OcorrenciaModel:
        """Atualiza o status de uma ocorrência."""
        ocorrencia.status = new_status
        self.db.commit()
        self.db.refresh(ocorrencia)
        return ocorrencia

    def delete(self, ocorrencia: OcorrenciaModel) -> None:
        """Remove uma ocorrência do banco."""
        self.db.delete(ocorrencia)
        self.db.commit()

    def batch_resolve(self) -> int:
        """Resolve todas as ocorrências não resolvidas. Retorna o número de afetadas."""
        affected = self.db.query(OcorrenciaModel).filter(
            OcorrenciaModel.status != "resolvido"
        ).update(
            {OcorrenciaModel.status: "resolvido"},
            synchronize_session=False,
        )
        self.db.commit()
        return affected
