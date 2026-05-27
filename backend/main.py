import os
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationInfo
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from dotenv import load_dotenv
import jwt
import time
from sqlalchemy.exc import OperationalError
import bcrypt

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/urbanacare")

# Database Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security & JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_CHANGEME_IN_PRODUCTION_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Password helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# JWT helper functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# SQLAlchemy Models
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(30), default="user", nullable=False)  # "user" or "admin"
    reset_token = Column(String(100), nullable=True) # Mock reset token for password recovery
    
    ocorrencias = relationship("OcorrenciaModel", back_populates="owner")

class FeatureToggleModel(Base):
    __tablename__ = "feature_toggles"

    key = Column(String(50), primary_key=True, index=True)
    value = Column(Boolean, default=True, nullable=False)

class OcorrenciaModel(Base):
    __tablename__ = "ocorrencias"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    status = Column(String(30), default="pendente", nullable=False)
    photo = Column(String(500), nullable=True)
    type = Column(String(30), default="urbana", nullable=False) # "urbana" or "pessoal"
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("UserModel", back_populates="ocorrencias")

# Tables will be created at startup with retry logic

# Pydantic Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    email: str
    role: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    token: str
    new_password: str = Field(..., min_length=6)

class ToggleResponse(BaseModel):
    key: str
    value: bool

    class Config:
        from_attributes = True

CATEGORIES_AND_TYPES = {
    "infraestrutura": ["buracos em ruas", "problemas de infraestrutura"],
    "iluminação": ["iluminação pública quebrada"],
    "limpeza urbana": ["lixo acumulado", "descarte irregular de lixo"],
    "trânsito": ["sinalização danificada"],
    "saneamento": ["vazamentos"],
    "segurança pública": ["assaltos", "furtos", "vandalismo", "riscos à segurança pública"],
    "meio ambiente": ["poluição", "problemas ambientais"],
    "saúde urbana": ["focos de dengue"],
    "proteção animal": ["animais abandonados"],
    "emergências urbanas": ["situações de risco urbano"]
}

class OcorrenciaBase(BaseModel):
    title: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    description: str
    lat: float
    lng: float
    photo: Optional[str] = Field(None, max_length=500)
    type: str = Field(..., max_length=30)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORIES_AND_TYPES:
            raise ValueError(f"Categoria inválida: {v}")
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str, info: ValidationInfo) -> str:
        category = info.data.get("category")
        if not category:
            return v
        valid_types = CATEGORIES_AND_TYPES.get(category, [])
        if v not in valid_types:
            raise ValueError(f"Tipo de ocorrência '{v}' não pertence à categoria '{category}'")
        return v

class OcorrenciaCreate(OcorrenciaBase):
    pass

class OcorrenciaStatusUpdate(BaseModel):
    status: str = Field(..., max_length=30)

class OcorrenciaResponse(OcorrenciaBase):
    id: int
    status: str
    date: datetime
    user_id: Optional[int] = None

    class Config:
        from_attributes = True

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth Dependency
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível autenticar o token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(current_user: UserModel = Depends(get_current_user)) -> UserModel:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita a administradores"
        )
    return current_user

# Get specific toggle helper
def get_toggle_value(db: Session, key: str, default: bool = True) -> bool:
    toggle = db.query(FeatureToggleModel).filter(FeatureToggleModel.key == key).first()
    if not toggle:
        return default
    return toggle.value

# Seed Data logic
def seed_database(db: Session):
    # 1. Seed Feature Toggles
    default_toggles = {
        "allow_personal_occurrences": True,
        "allow_mock_photos": True,
        "read_only_mode": False
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
            role="admin"
        ))
        
    user_email = "cidadao@exemplo.com"
    if not db.query(UserModel).filter(UserModel.email == user_email).first():
        db.add(UserModel(
            email=user_email,
            hashed_password=get_password_hash("senha123"),
            role="user"
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
                user_id=admin_id
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
                user_id=admin_id
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
                user_id=admin_id
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
                user_id=admin_id
            )
        ]
        db.add_all(mock_data)
        db.commit()

def init_db_with_retry():
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

# FastAPI App Setup
app = FastAPI(title="UrbanaCare API Pro", description="API de Gerenciamento de Ocorrências com Autenticação e Admin Dashboard")

@app.on_event("startup")
def startup_event():
    init_db_with_retry()

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- AUTHENTICATION ROUTES -----------------

@app.post("/api/auth/register", response_model=UserResponse)
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    # Check if exists
    exists = db.query(UserModel).filter(UserModel.email == user.email).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já está cadastrado."
        )
        
    db_user = UserModel(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        role="user"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/auth/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user.email,
        "role": user.role
    }

@app.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == req.email).first()
    if not user:
        # Avoid user enumeration, pretend it was sent anyway
        return {"message": "Caso o e-mail exista, um código de redefinição foi gerado."}
        
    # Generate mock reset token
    reset_token = f"reset-{int(datetime.utcnow().timestamp())}"
    user.reset_token = reset_token
    db.commit()
    
    # PRINT IN CONTAINER LOG FOR USER ACCESS
    print("\n" + "="*80)
    print(f"MOCK PASSWORD RESET LINK FOR: {user.email}")
    print(f"Use the token: {reset_token}")
    print(f"Redefinition parameters: ?email={user.email}&token={reset_token}")
    print("="*80 + "\n")
    
    return {
        "message": "Caso o e-mail exista, um código de redefinição foi gerado. Verifique os logs do Docker para resgatar seu link.",
        "debug_token": reset_token # Send directly for UI developer ease
    }

@app.post("/api/auth/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.email == req.email).first()
    if not user or user.reset_token != req.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de redefinição inválido ou e-mail inválido."
        )
        
    user.hashed_password = get_password_hash(req.new_password)
    user.reset_token = None
    db.commit()
    return {"message": "Senha redefinida com sucesso."}

@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_profile(current_user: UserModel = Depends(get_current_user)):
    return current_user


# ----------------- OCCURRENCES ROUTES -----------------

@app.get("/api/ocorrencias", response_model=List[OcorrenciaResponse])
def list_ocorrencias(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    allow_personal = get_toggle_value(db, "allow_personal_occurrences", True)
    
    query = db.query(OcorrenciaModel)
    
    if category:
        query = query.filter(OcorrenciaModel.category == category)
    if status:
        query = query.filter(OcorrenciaModel.status == status)
        
    # If personal occurrences are disabled via admin toggle, hide security-related ones
    if not allow_personal:
        query = query.filter(OcorrenciaModel.category != "segurança pública")
        
    return query.order_by(OcorrenciaModel.date.desc()).all()

@app.post("/api/ocorrencias", response_model=OcorrenciaResponse, status_code=status.HTTP_201_CREATED)
def create_ocorrencia(
    ocorrencia: OcorrenciaCreate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check Read-Only Mode toggle
    read_only = get_toggle_value(db, "read_only_mode", False)
    if read_only and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A plataforma está no modo SOMENTE LEITURA por ordem administrativa."
        )
        
    # Check Personal Occurrences toggle
    allow_personal = get_toggle_value(db, "allow_personal_occurrences", True)
    if ocorrencia.category == "segurança pública" and not allow_personal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O cadastro de ocorrências de segurança pública foi desativado temporariamente."
        )

    db_ocorrencia = OcorrenciaModel(
        title=ocorrencia.title,
        category=ocorrencia.category,
        description=ocorrencia.description,
        lat=ocorrencia.lat,
        lng=ocorrencia.lng,
        photo=ocorrencia.photo,
        type=ocorrencia.type,
        status="pendente",
        user_id=current_user.id,
        date=datetime.utcnow()
    )
    db.add(db_ocorrencia)
    db.commit()
    db.refresh(db_ocorrencia)
    return db_ocorrencia

@app.patch("/api/ocorrencias/{ocorrencia_id}/status", response_model=OcorrenciaResponse)
def update_ocorrencia_status(
    ocorrencia_id: int,
    status_update: OcorrenciaStatusUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check Read-Only Mode toggle
    read_only = get_toggle_value(db, "read_only_mode", False)
    if read_only and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A plataforma está no modo SOMENTE LEITURA por ordem administrativa."
        )

    db_ocorrencia = db.query(OcorrenciaModel).filter(OcorrenciaModel.id == ocorrencia_id).first()
    if not db_ocorrencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ocorrência não encontrada."
        )
        
    # Only the owner or an admin can update occurrence status
    if db_ocorrencia.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissões para alterar esta ocorrência."
        )
        
    db_ocorrencia.status = status_update.status
    db.commit()
    db.refresh(db_ocorrencia)
    return db_ocorrencia

@app.delete("/api/ocorrencias/{ocorrencia_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ocorrencia(
    ocorrencia_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check Read-Only Mode toggle
    read_only = get_toggle_value(db, "read_only_mode", False)
    if read_only and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A plataforma está no modo SOMENTE LEITURA por ordem administrativa."
        )

    db_ocorrencia = db.query(OcorrenciaModel).filter(OcorrenciaModel.id == ocorrencia_id).first()
    if not db_ocorrencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ocorrência não encontrada."
        )
        
    # Only owner or admin can delete
    if db_ocorrencia.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para excluir esta ocorrência."
        )
        
    db.delete(db_ocorrencia)
    db.commit()
    return None


# ----------------- ADMIN DASHBOARD ROUTES -----------------

@app.get("/api/admin/toggles", response_model=List[ToggleResponse])
def get_toggles(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return db.query(FeatureToggleModel).all()

@app.post("/api/admin/toggles", response_model=ToggleResponse)
def update_toggle(
    key: str = Body(..., embed=True),
    value: bool = Body(..., embed=True),
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    toggle = db.query(FeatureToggleModel).filter(FeatureToggleModel.key == key).first()
    if not toggle:
        toggle = FeatureToggleModel(key=key, value=value)
        db.add(toggle)
    else:
        toggle.value = value
        
    db.commit()
    db.refresh(toggle)
    return toggle

@app.post("/api/admin/batch-resolve")
def batch_resolve_occurrences(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    # Resolve all non-resolved occurrences
    affected = db.query(OcorrenciaModel).filter(OcorrenciaModel.status != "resolvido").update(
        {OcorrenciaModel.status: "resolvido"},
        synchronize_session=False
    )
    db.commit()
    return {"message": f"Ação executada com sucesso. {affected} ocorrências foram resolvidas."}

@app.get("/api/admin/users", response_model=List[UserResponse])
def list_users(
    current_user: UserModel = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return db.query(UserModel).order_by(UserModel.id.asc()).all()
