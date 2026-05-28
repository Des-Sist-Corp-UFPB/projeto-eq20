"""Seed de dados iniciais e lógica de inicialização do banco."""

import time

from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.session import engine, SessionLocal
from app.models import Base, UserModel, OcorrenciaModel, FeatureToggleModel
from app.security.password import get_password_hash


def seed_database(db: Session) -> None:
    """Popula o banco de dados com dados iniciais se necessário."""

    # 1. Seed Feature Toggles
    default_toggles = {
        "allow_personal_occurrences": True,
        "allow_mock_photos": True,
        "read_only_mode": False,
    }
    for k, v in default_toggles.items():
        if not db.query(FeatureToggleModel).filter(FeatureToggleModel.key == k).first():
            db.add(FeatureToggleModel(key=k, value=v))

    # 2. Seed Admin and User
    admin_email = "admin@urbanacare.com"
    if not db.query(UserModel).filter(UserModel.email == admin_email).first():
        db.add(UserModel(
            email=admin_email,
            hashed_password=get_password_hash("admin123"),
            role="admin",
        ))

    user_email = "cidadao@exemplo.com"
    if not db.query(UserModel).filter(UserModel.email == user_email).first():
        db.add(UserModel(
            email=user_email,
            hashed_password=get_password_hash("senha123"),
            role="user",
        ))

    db.commit()

    # 3. Seed Mock Occurrences if empty
    if db.query(OcorrenciaModel).count() == 0:
        admin_user = db.query(UserModel).filter(UserModel.email == admin_email).first()
        admin_id = admin_user.id if admin_user else None

        mock_data = [
            OcorrenciaModel(
                title="Cratera profunda na faixa de ônibus",
                category="infraestrutura",
                description="Buraco muito fundo na via principal perto da parada de ônibus da reitoria. Carros estão tendo que desviar invadindo a outra pista, com grande risco de colisão.",
                lat=-7.1378,
                lng=-34.8475,
                status="pendente",
                type="buracos em ruas",
                photo="https://images.unsplash.com/photo-1515162305285-0293e4767cc2?w=500&auto=format&fit=crop",
                user_id=admin_id,
            ),
            OcorrenciaModel(
                title="Lâmpadas queimadas no estacionamento do CT",
                category="iluminação",
                description="Três postes de iluminação estão completamente apagados no estacionamento lateral do Centro de Tecnologia. Muito escuro à noite, gerando insegurança para os estudantes.",
                lat=-7.1350,
                lng=-34.8432,
                status="progresso",
                type="iluminação pública quebrada",
                photo="https://images.unsplash.com/photo-1509024644558-2f56ce76c490?w=500&auto=format&fit=crop",
                user_id=admin_id,
            ),
            OcorrenciaModel(
                title="Assalto armado no ponto de ônibus",
                category="segurança pública",
                description="Dois indivíduos de bicicleta abordaram estudantes que esperavam o ônibus noturno levando celulares e mochilas. Zona perigosa.",
                lat=-7.1345,
                lng=-34.8480,
                status="pendente",
                type="assaltos",
                photo="https://images.unsplash.com/photo-1508432296123-c4ec3e17529f?w=500&auto=format&fit=crop",
                user_id=admin_id,
            ),
            OcorrenciaModel(
                title="Vazamento contínuo de água limpa",
                category="saneamento",
                description="Vazamento volumoso na calçada do bloco de biologia. A água está jorrando há mais de 24h e inundando a rampa de acessibilidade.",
                lat=-7.1331,
                lng=-34.8445,
                status="pendente",
                type="vazamentos",
                photo="https://images.unsplash.com/photo-1542044896530-05d85be9b11a?w=500&auto=format&fit=crop",
                user_id=admin_id,
            ),
        ]
        db.add_all(mock_data)
        db.commit()


def init_db_with_retry() -> None:
    """Inicializa o banco de dados com lógica de retry para aguardar o PostgreSQL."""
    max_retries = 10
    retry_interval = 2
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Tentando conectar ao banco de dados... (Tentativa {attempt}/{max_retries})")
            connection = engine.connect()
            connection.close()
            print("Conexão estabelecida com sucesso!")

            # Create tables
            Base.metadata.create_all(bind=engine)

            # Seed default values
            with SessionLocal() as db_session:
                seed_database(db_session)
            return
        except OperationalError as e:
            if attempt == max_retries:
                print(f"Erro fatal: Não foi possível conectar ao banco de dados após {max_retries} tentativas.")
                raise e
            print(f"Banco de dados indisponível no momento. Aguardando {retry_interval} segundos...")
            time.sleep(retry_interval)
