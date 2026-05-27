import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    # Auto-create tables for SQLite test session
    Base.metadata.create_all(bind=engine)
    
    # Seed default values for tests
    from main import FeatureToggleModel, UserModel, get_password_hash
    db = TestingSessionLocal()
    
    db.add(FeatureToggleModel(key="allow_personal_occurrences", value=True))
    db.add(FeatureToggleModel(key="allow_mock_photos", value=True))
    db.add(FeatureToggleModel(key="read_only_mode", value=False))
    
    db.add(UserModel(
        email="admin@urbanacare.com", 
        hashed_password=get_password_hash("admin123"), 
        role="admin"
    ))
    db.add(UserModel(
        email="cidadao@exemplo.com", 
        hashed_password=get_password_hash("senha123"), 
        role="user"
    ))
    
    db.commit()
    db.close()
    
    yield
    # Drop all tables after test finished
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_register_and_login():
    # Register new user
    response = client.post(
        "/api/auth/register",
        json={"email": "novo.cidadao@teste.com", "password": "novasenha123"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "novo.cidadao@teste.com"

    # Login and check JWT Token
    response = client.post(
        "/api/auth/login",
        data={"username": "novo.cidadao@teste.com", "password": "novasenha123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "novo.cidadao@teste.com"
    assert data["role"] == "user"

def test_create_occurrence_unauthenticated():
    # Try to post an occurrence without authorization header
    response = client.post(
        "/api/ocorrencias",
        json={
            "title": "Buraco na pista",
            "category": "infraestrutura",
            "description": "Buraco de grande proporção no asfalto",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "buracos em ruas"
        }
    )
    # Must fail because no token was passed
    assert response.status_code == 401

def test_list_occurrences():
    # Public route to fetch occurrences list
    response = client.get("/api/ocorrencias")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_occurrence_validation():
    # 1. Login to get token
    login_response = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Try valid category and type
    response = client.post(
        "/api/ocorrencias",
        json={
            "title": "Buraco na rua principal",
            "category": "infraestrutura",
            "description": "Buraco grande na rua principal",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "buracos em ruas"
        },
        headers=headers
    )
    assert response.status_code == 201
    assert response.json()["category"] == "infraestrutura"
    assert response.json()["type"] == "buracos em ruas"

    # 3. Try invalid category
    response = client.post(
        "/api/ocorrencias",
        json={
            "title": "Buraco na rua principal",
            "category": "invalid_category",
            "description": "Buraco grande na rua principal",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "buracos em ruas"
        },
        headers=headers
    )
    assert response.status_code == 422

    # 4. Try invalid type for category
    response = client.post(
        "/api/ocorrencias",
        json={
            "title": "Buraco na rua principal",
            "category": "infraestrutura",
            "description": "Buraco grande na rua principal",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "vazamentos"
        },
        headers=headers
    )
    assert response.status_code == 422
