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
        email="admin@riou.com", 
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


def test_authorization_and_ban():
    # 1. Login as admin to manage users
    admin_login = client.post(
        "/api/auth/login",
        data={"username": "admin@riou.com", "password": "admin123"}
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Get list of users and find standard user ID
    users_resp = client.get("/api/admin/users", headers=admin_headers)
    assert users_resp.status_code == 200
    users = users_resp.json()
    user_id = next(u["id"] for u in users if u["role"] == "user")

    # 3. Create an occurrence as standard user
    user_login = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    assert user_login.status_code == 200
    user_data = user_login.json()
    user_token = user_data["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # Create occurrence
    occ_resp = client.post(
        "/api/ocorrencias",
        json={
            "title": "Ocorrência do Cidadão",
            "category": "infraestrutura",
            "description": "Buraco na calçada",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "buracos em ruas"
        },
        headers=user_headers
    )
    assert occ_resp.status_code == 201
    occ_id = occ_resp.json()["id"]

    # 4. Try to change status of occurrence as standard user (must FAIL - 403)
    status_resp = client.patch(
        f"/api/ocorrencias/{occ_id}/status",
        json={"status": "progresso"},
        headers=user_headers
    )
    assert status_resp.status_code == 403

    # Change status as admin (must PASS)
    status_resp = client.patch(
        f"/api/ocorrencias/{occ_id}/status",
        json={"status": "progresso"},
        headers=admin_headers
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "progresso"

    # 5. Ban the user for 60 minutes
    ban_resp = client.post(
        f"/api/admin/users/{user_id}/ban",
        json={"duration_minutes": 60},
        headers=admin_headers
    )
    assert ban_resp.status_code == 200
    assert ban_resp.json()["banned_until"] is not None

    # Try to login as banned user (must FAIL - 403)
    banned_login = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    assert banned_login.status_code == 403
    assert "temporariamente banida" in banned_login.json()["detail"]

    # Try to use banned user's existing token (must FAIL - 403)
    banned_post = client.post(
        "/api/ocorrencias",
        json={
            "title": "Buraco na via principal",
            "category": "infraestrutura",
            "description": "Buraco grande na rua principal",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "buracos em ruas"
        },
        headers=user_headers
    )
    assert banned_post.status_code == 403

    # Unban user
    unban_resp = client.post(
        f"/api/admin/users/{user_id}/ban",
        json={"duration_minutes": 0},
        headers=admin_headers
    )
    assert unban_resp.status_code == 200
    assert unban_resp.json()["banned_until"] is None

    # 6. Test delete occurrences permissions
    # Another standard user cannot delete it
    client.post(
        "/api/auth/register",
        json={"email": "outro@teste.com", "password": "outrasenha123"}
    )
    outro_login = client.post(
        "/api/auth/login",
        data={"username": "outro@teste.com", "password": "outrasenha123"}
    )
    outro_token = outro_login.json()["access_token"]
    outro_headers = {"Authorization": f"Bearer {outro_token}"}

    del_resp1 = client.delete(f"/api/ocorrencias/{occ_id}", headers=outro_headers)
    assert del_resp1.status_code == 403

    # The owner CAN delete it
    re_login = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    re_token = re_login.json()["access_token"]
    re_headers = {"Authorization": f"Bearer {re_token}"}
    del_resp2 = client.delete(f"/api/ocorrencias/{occ_id}", headers=re_headers)
    assert del_resp2.status_code == 204
