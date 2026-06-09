"""Modelo de ocorrência."""

from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.models.base import Base

# Tabela de associação para rastrear quais usuários declararam-se afetados por quais ocorrências
ocorrencia_afetados = Table(
    "ocorrencia_afetados",
    Base.metadata,
    Column("ocorrencia_id", Integer, ForeignKey("ocorrencias.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class OcorrenciaModel(Base):
    """Modelo SQLAlchemy para a tabela de ocorrências."""

    __tablename__ = "ocorrencias"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    status = Column(String(30), default="pendente", nullable=False)
    photo = Column(String(500), nullable=True)
    type = Column(String(30), default="urbana", nullable=False)  # "urbana" or "pessoal"
    date = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    owner = relationship("UserModel", back_populates="ocorrencias")
    
    # Relação N:M com os usuários que foram afetados por esta ocorrência
    afetados = relationship("UserModel", secondary=ocorrencia_afetados, backref="ocorrencias_afetadas")

    def get_urgency_score(self) -> float:
        """Calcula o nível de urgência com base no tempo de criação e nas pessoas afetadas."""
        from datetime import datetime, UTC, timezone
        now = datetime.now(UTC)
        date_val = self.date
        if date_val.tzinfo is None:
            # Assume que a data salva no banco é UTC naive
            date_val = date_val.replace(tzinfo=timezone.utc)
            
        elapsed_seconds = (now - date_val).total_seconds()
        elapsed_hours = max(0.0, elapsed_seconds / 3600.0)
        
        # Cada pessoa afetada aumenta a urgência equivalente a 24 horas adicionais de espera
        affected_count = len(self.afetados) if self.afetados else 0
        return elapsed_hours + (affected_count * 24.0)

