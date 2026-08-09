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
    # 1. Register new user (returns message that code was sent)
    response = client.post(
        "/api/auth/register",
        json={"email": "novo.cidadao@teste.com", "password": "novasenha123"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "novo.cidadao@teste.com"

    # 2. Get code from database
    from app.models.pending_registration import PendingRegistrationModel
    db = TestingSessionLocal()
    pending = db.query(PendingRegistrationModel).filter_by(email="novo.cidadao@teste.com").first()
    assert pending is not None
    code = pending.code
    db.close()

    # 3. Try to verify with an incorrect code (should fail)
    response = client.post(
        "/api/auth/verify-register",
        json={"email": "novo.cidadao@teste.com", "code": "000000"}
    )
    assert response.status_code == 400

    # 4. Verify with the correct code (should succeed)
    response = client.post(
        "/api/auth/verify-register",
        json={"email": "novo.cidadao@teste.com", "code": code}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "novo.cidadao@teste.com"

    # 5. Login and check JWT Token
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
    # Try to post an occurrence without authorization header (should succeed in anonymous mode)
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
    assert response.status_code == 201
    data = response.json()
    assert data["creator_name"] == "Anônimo"
    assert data["user_id"] is None

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
    from app.models.pending_registration import PendingRegistrationModel
    db = TestingSessionLocal()
    pending = db.query(PendingRegistrationModel).filter_by(email="outro@teste.com").first()
    assert pending is not None
    code = pending.code
    db.close()
    
    client.post(
        "/api/auth/verify-register",
        json={"email": "outro@teste.com", "code": code}
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


def test_upload_file(monkeypatch):
    mock_url = "https://s3.dsc.rodrigor.com/eq20/mocked_image.png"
    def mock_upload(file_content, file_name, content_type):
        return mock_url

    import app.services.storage_service
    monkeypatch.setattr(app.services.storage_service, "upload_file_to_s3", mock_upload)

    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Post multipart file
    file_payload = {"file": ("test_image.png", b"fake image content", "image/png")}
    response = client.post(
        "/api/ocorrencias/upload",
        files=file_payload,
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["url"] == mock_url

    # Post invalid mime file format (should return 400)
    file_payload_invalid = {"file": ("test_doc.txt", b"plain text", "text/plain")}
    response = client.post(
        "/api/ocorrencias/upload",
        files=file_payload_invalid,
        headers=headers
    )
    assert response.status_code == 400

    # Post where upload function raises exception (should return 500)
    def mock_upload_error(*args, **kwargs):
        raise Exception("Mock storage error")
    monkeypatch.setattr(app.services.storage_service, "upload_file_to_s3", mock_upload_error)
    response = client.post(
        "/api/ocorrencias/upload",
        files=file_payload,
        headers=headers
    )
    assert response.status_code == 500



def test_occurrence_prioritization_and_affected():
    # 1. Login Creator (cidadao)
    login_resp = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    creator_token = login_resp.json()["access_token"]
    creator_headers = {"Authorization": f"Bearer {creator_token}"}

    # Register and Login User 2
    client.post(
        "/api/auth/register",
        json={"email": "user2@exemplo.com", "password": "password123"}
    )
    from app.models.pending_registration import PendingRegistrationModel
    db = TestingSessionLocal()
    pending = db.query(PendingRegistrationModel).filter_by(email="user2@exemplo.com").first()
    assert pending is not None
    code = pending.code
    db.close()

    client.post(
        "/api/auth/verify-register",
        json={"email": "user2@exemplo.com", "code": code}
    )
    login_resp2 = client.post(
        "/api/auth/login",
        data={"username": "user2@exemplo.com", "password": "password123"}
    )
    user2_token = login_resp2.json()["access_token"]
    user2_headers = {"Authorization": f"Bearer {user2_token}"}

    # Login Admin
    admin_login = client.post(
        "/api/auth/login",
        data={"username": "admin@riou.com", "password": "admin123"}
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Creator creates two occurrences (Occ A and Occ B)
    occ_a_resp = client.post(
        "/api/ocorrencias",
        json={
            "title": "Buraco A",
            "category": "infraestrutura",
            "description": "Buraco grande A",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "buracos em ruas"
        },
        headers=creator_headers
    )
    assert occ_a_resp.status_code == 201
    occ_a_id = occ_a_resp.json()["id"]

    occ_b_resp = client.post(
        "/api/ocorrencias",
        json={
            "title": "Buraco B",
            "category": "infraestrutura",
            "description": "Buraco grande B",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "buracos em ruas"
        },
        headers=creator_headers
    )
    assert occ_b_resp.status_code == 201
    occ_b_id = occ_b_resp.json()["id"]

    # 3. Creator tries to toggle affected on Occ A (must fail - 400)
    toggle_creator_resp = client.post(
        f"/api/ocorrencias/{occ_a_id}/toggle-afetado",
        headers=creator_headers
    )
    assert toggle_creator_resp.status_code == 400
    assert "criador da ocorrência não pode declarar-se afetado" in toggle_creator_resp.json()["detail"]

    # 4. User 2 toggles affected on Occ A (must pass - 200)
    toggle_user2_resp = client.post(
        f"/api/ocorrencias/{occ_a_id}/toggle-afetado",
        headers=user2_headers
    )
    assert toggle_user2_resp.status_code == 200
    assert toggle_user2_resp.json()["is_affected"] is True

    # 5. User 2 lists occurrences: affected_count and urgency_score must be None/hidden
    list_user2_resp = client.get("/api/ocorrencias", headers=user2_headers)
    assert list_user2_resp.status_code == 200
    occ_a_data = next(o for o in list_user2_resp.json() if o["id"] == occ_a_id)
    assert occ_a_data["is_affected"] is True
    assert occ_a_data["affected_count"] is None
    assert occ_a_data["urgency_score"] is None

    # 6. Admin lists occurrences:
    # Occ A must have affected_count = 1
    # Occ A must be returned BEFORE Occ B (sorted by urgency, since they have same time but Occ A has 1 affected)
    list_admin_resp = client.get("/api/ocorrencias", headers=admin_headers)
    assert list_admin_resp.status_code == 200
    admin_occurrences = list_admin_resp.json()
    
    occ_a_admin = next(o for o in admin_occurrences if o["id"] == occ_a_id)
    assert occ_a_admin["affected_count"] == 1
    assert occ_a_admin["urgency_score"] is not None

    occ_b_admin = next(o for o in admin_occurrences if o["id"] == occ_b_id)
    assert occ_b_admin["affected_count"] == 0

    # Index of Occ A must be smaller than Index of Occ B (higher urgency first)
    index_a = next(i for i, o in enumerate(admin_occurrences) if o["id"] == occ_a_id)
    index_b = next(i for i, o in enumerate(admin_occurrences) if o["id"] == occ_b_id)
    assert index_a < index_b

    # 7. User 2 untoggles affected on Occ A
    toggle_user2_again = client.post(
        f"/api/ocorrencias/{occ_a_id}/toggle-afetado",
        headers=user2_headers
    )
    assert toggle_user2_again.status_code == 200
    assert toggle_user2_again.json()["is_affected"] is False

    # Admin lists again, affected_count must be 0 now
    list_admin_resp_2 = client.get("/api/ocorrencias", headers=admin_headers)
    occ_a_admin_2 = next(o for o in list_admin_resp_2.json() if o["id"] == occ_a_id)
    assert occ_a_admin_2["affected_count"] == 0


def test_audit_logs():
    # 1. Try to fetch audit logs unauthenticated (must fail)
    response = client.get("/api/admin/audit-logs")
    assert response.status_code == 401

    # 2. Login as normal user and try to fetch (must fail - 403)
    user_login = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get("/api/admin/audit-logs", headers=user_headers)
    assert response.status_code == 403

    # 3. Login as admin
    admin_login = client.post(
        "/api/auth/login",
        data={"username": "admin@riou.com", "password": "admin123"}
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 4. Fetch audit logs (should pass)
    response = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    
    # In setup_db or our login calls, there should be LOGIN actions
    login_logs = [l for l in logs if l["action"] == "LOGIN"]
    assert len(login_logs) >= 1

    # 5. Admin updates a feature toggle
    toggle_resp = client.post(
        "/api/admin/toggles",
        json={"key": "read_only_mode", "value": True},
        headers=admin_headers
    )
    assert toggle_resp.status_code == 200

    # 6. Fetch logs again and verify the action ADMIN_TOGGLE_UPDATE is recorded
    response = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert response.status_code == 200
    logs = response.json()
    toggle_logs = [l for l in logs if l["action"] == "ADMIN_TOGGLE_UPDATE"]
    assert len(toggle_logs) == 1
    assert toggle_logs[0]["resource"] == "feature_toggle"
    assert toggle_logs[0]["resource_id"] == "read_only_mode"
    assert "True" in toggle_logs[0]["details"]


def test_auth_service_extended():
    db = TestingSessionLocal()
    from app.services.auth_service import AuthService
    from app.schemas.user import UserRegister
    service = AuthService(db)

    # 1. Register user that already exists
    with pytest.raises(Exception) as excinfo:
        service.register(UserRegister(email="cidadao@exemplo.com", password="password123"))
    assert "já está cadastrado" in str(excinfo.value)

    # 2. Verify register with email that has no pending registration
    with pytest.raises(Exception) as excinfo:
        service.verify_register("nao_existe@teste.com", "123456")
    assert "cadastro pendente" in str(excinfo.value)

    # 3. Verify register with wrong code
    # We must create a pending first
    service.register(UserRegister(email="novo_pendente@teste.com", password="password123"))
    with pytest.raises(Exception) as excinfo:
        service.verify_register("novo_pendente@teste.com", "000000")
    assert "Código de verificação inválido" in str(excinfo.value)

    # 4. Verify register with expired code
    from app.models.pending_registration import PendingRegistrationModel
    from datetime import datetime, timedelta, timezone
    pending = db.query(PendingRegistrationModel).filter_by(email="novo_pendente@teste.com").first()
    pending.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db.commit()
    with pytest.raises(Exception) as excinfo:
        service.verify_register("novo_pendente@teste.com", pending.code)
    assert "Código de verificação expirado" in str(excinfo.value)

    # 5. Forgot password for user that does not exist (should return generic message without raising)
    res = service.forgot_password("inexistente_de_verdade@teste.com")
    assert "Caso o e-mail exista" in res["message"]

    # 6. Forgot password for user that DOES exist (should generate reset token successfully)
    res_exist = service.forgot_password("cidadao@exemplo.com")
    assert "Caso o e-mail exista" in res_exist["message"] or "logs do Docker" in res_exist["message"]

    # 7. Reset password with invalid token
    with pytest.raises(Exception) as excinfo:
        service.reset_password("cidadao@exemplo.com", "token_invalido", "senha123456")
    assert "Token de redefinição inválido" in str(excinfo.value)

    # 8. Reset password for user that does not exist
    with pytest.raises(Exception) as excinfo:
        service.reset_password("nao_existente_user@teste.com", "any_token", "senha123456")
    assert "Token de redefinição inválido" in str(excinfo.value)

    # 9. Login with user that doesn't exist
    with pytest.raises(Exception) as excinfo:
        service.login("inexistente_de_verdade@teste.com", "senha123")
    assert "E-mail ou senha incorretos" in str(excinfo.value)

    db.close()


def test_admin_service_extended():
    db = TestingSessionLocal()
    from app.services.admin_service import AdminService
    from app.models.user import UserModel
    service = AdminService(db)
    
    admin_user = db.query(UserModel).filter_by(email="admin@riou.com").first()

    # 1. Ban user that does not exist
    with pytest.raises(Exception) as excinfo:
        service.ban_user(9999, 60, admin_user)
    assert "Usuário não encontrado" in str(excinfo.value)

    # 2. Ban an admin
    with pytest.raises(Exception) as excinfo:
        service.ban_user(admin_user.id, 60, admin_user)
    assert "Não é possível banir um administrador" in str(excinfo.value)

    # 3. Delete user that does not exist
    with pytest.raises(Exception) as excinfo:
        service.delete_user(9999, admin_user)
    assert "Usuário não encontrado" in str(excinfo.value)

    # 4. Delete an admin
    with pytest.raises(Exception) as excinfo:
        service.delete_user(admin_user.id, admin_user)
    assert "Não é possível excluir um administrador" in str(excinfo.value)

    # 5. Delete a standard user successfully
    # Create standard user
    std_user = service.user_repo.create("std_to_delete@teste.com", "senha123")
    service.delete_user(std_user.id, admin_user)
    assert service.user_repo.get_by_id(std_user.id) is None

    db.close()

    # 6. Fetch toggles list using admin client
    admin_login = client.post(
        "/api/auth/login",
        data={"username": "admin@riou.com", "password": "admin123"}
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/admin/toggles", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_ocorrencia_service_extended():
    # Setup tokens
    admin_login = client.post(
        "/api/auth/login",
        data={"username": "admin@riou.com", "password": "admin123"}
    )
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    user_login = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    user_token = user_login.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Update status of non-existent occurrence
    response = client.patch(
        "/api/ocorrencias/9999/status",
        json={"status": "progresso"},
        headers=admin_headers
    )
    assert response.status_code == 404

    # 2. Delete non-existent occurrence
    response = client.delete(
        "/api/ocorrencias/9999",
        headers=user_headers
    )
    assert response.status_code == 404

    # 3. Toggle affected on non-existent occurrence
    response = client.post(
        "/api/ocorrencias/9999/toggle-afetado",
        headers=user_headers
    )
    assert response.status_code == 404

    # 4. Read-Only Mode Restrictions
    # Enable Read-Only Mode
    client.post(
        "/api/admin/toggles",
        json={"key": "read_only_mode", "value": True},
        headers=admin_headers
    )

    # Try to create occurrence (should fail 403)
    response = client.post(
        "/api/ocorrencias",
        json={
            "title": "Buraco no modo somente leitura",
            "category": "infraestrutura",
            "description": "Buraco grande",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "buracos em ruas"
        },
        headers=user_headers
    )
    assert response.status_code == 403

    # Try to update status as user (should fail 403)
    response = client.patch(
        "/api/ocorrencias/1/status",
        json={"status": "progresso"},
        headers=user_headers
    )
    assert response.status_code == 403

    # Try to toggle affected as user (should fail 403)
    response = client.post(
        "/api/ocorrencias/1/toggle-afetado",
        headers=user_headers
    )
    assert response.status_code == 403

    # Try to delete occurrence as user (should fail 403)
    response = client.delete(
        "/api/ocorrencias/1",
        headers=user_headers
    )
    assert response.status_code == 403

    # Disable Read-Only Mode
    client.post(
        "/api/admin/toggles",
        json={"key": "read_only_mode", "value": False},
        headers=admin_headers
    )

    # 5. Allow Personal Occurrences toggle restrictions
    # Disable personal occurrences
    client.post(
        "/api/admin/toggles",
        json={"key": "allow_personal_occurrences", "value": False},
        headers=admin_headers
    )

    # Try to create security public (segurança pública) occurrence (should fail 403)
    response = client.post(
        "/api/ocorrencias",
        json={
            "title": "Assalto no ponto",
            "category": "segurança pública",
            "description": "Assalto armado",
            "lat": -7.1355,
            "lng": -34.8421,
            "type": "assaltos"
        },
        headers=user_headers
    )
    assert response.status_code == 403

    # Reset toggle
    client.post(
        "/api/admin/toggles",
        json={"key": "allow_personal_occurrences", "value": True},
        headers=admin_headers
    )


def test_storage_service_unit(monkeypatch):
    import boto3
    from unittest.mock import MagicMock
    from botocore.exceptions import ClientError
    from app.services.storage_service import init_s3, upload_file_to_s3
    
    mock_s3 = MagicMock()
    # Mock head_bucket throwing NoSuchBucket 404 ClientError
    err_response = {"Error": {"Code": "404"}}
    mock_s3.head_bucket.side_effect = ClientError(err_response, "head_bucket")
    monkeypatch.setattr(boto3, "client", lambda *args, **kwargs: mock_s3)
    
    # Run init_s3
    init_s3()
    assert mock_s3.create_bucket.called
    
    # Run upload_file_to_s3
    url = upload_file_to_s3(b"fake image", "image.png", "image/png")
    assert "image.png" in url

    # Mock head_bucket throwing other ClientError code to test else block
    err_response_other = {"Error": {"Code": "500"}}
    mock_s3.head_bucket.side_effect = ClientError(err_response_other, "head_bucket")
    with pytest.raises(ClientError):
        init_s3()


def test_email_service_unit(monkeypatch):
    from app.config.settings import settings
    from app.services.email_service import EmailService
    import smtplib
    
    monkeypatch.setattr(settings, "EMAIL_USER", "test@domain.com")
    monkeypatch.setattr(settings, "EMAIL_PASS", "test_pass")
    
    # Mock SMTP_SSL
    class MockSMTP_SSL:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args, **kwargs):
            pass
        def login(self, user, password):
            pass
        def sendmail(self, from_addr, to_addrs, msg):
            pass
            
    # Mock SMTP
    class MockSMTP:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args, **kwargs):
            pass
        def starttls(self, *args, **kwargs):
            pass
        def login(self, user, password):
            pass
        def sendmail(self, from_addr, to_addrs, msg):
            pass

    # Test success path for SSL (port 465)
    monkeypatch.setattr(settings, "SMTP_PORT", 465)
    monkeypatch.setattr(smtplib, "SMTP_SSL", MockSMTP_SSL)
    assert EmailService.send_verification_email("email@teste.com", "123456") is True

    # Test success path for TLS (port 587)
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(smtplib, "SMTP", MockSMTP)
    assert EmailService.send_verification_email("email@teste.com", "123456") is True

    # Test fallback path (exception when connecting)
    def raise_smtp_err(*args, **kwargs):
        raise Exception("SMTP Connection Failed")
    monkeypatch.setattr(smtplib, "SMTP", raise_smtp_err)
    assert EmailService.send_verification_email("email@teste.com", "123456") is True


def test_seed_database():
    db = TestingSessionLocal()
    from app.database.seed import seed_database, init_db_with_retry
    # Clear occurrences to test seed occurrences block
    from app.models.ocorrencia import OcorrenciaModel, ocorrencia_afetados
    db.execute(ocorrencia_afetados.delete())
    db.query(OcorrenciaModel).delete()
    db.commit()

    seed_database(db)
    assert db.query(OcorrenciaModel).count() > 0
    db.close()

    # Test init_db_with_retry
    init_db_with_retry()


def test_ping_and_spa():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dependencies_unauthorized():
    from app.security.dependencies import get_current_user, get_current_user_optional
    
    # Try invalid jwt
    with pytest.raises(Exception):
        get_current_user(token="invalid_token", db=TestingSessionLocal())
        
    # Try valid jwt but non-existent user
    from app.security.jwt import create_access_token
    token = create_access_token({"sub": "non_existent@user.com"})
    with pytest.raises(Exception):
        get_current_user(token=token, db=TestingSessionLocal())

    # Try token without sub
    token_no_sub = create_access_token({})
    with pytest.raises(Exception):
        get_current_user(token=token_no_sub, db=TestingSessionLocal())
    assert get_current_user_optional(token=token_no_sub, db=TestingSessionLocal()) is None
        
    # Try optional user with invalid token (should return None, not raise)
    assert get_current_user_optional(token="invalid_token", db=TestingSessionLocal()) is None
    
    # Try optional user with valid token but non-existent email (should return None, not raise)
    assert get_current_user_optional(token=token, db=TestingSessionLocal()) is None
    
    # Try optional user with banned user (should raise 403)
    db = TestingSessionLocal()
    from app.models.user import UserModel
    from datetime import datetime, UTC, timedelta
    user = db.query(UserModel).filter_by(email="cidadao@exemplo.com").first()
    user.banned_until = datetime.now(UTC) + timedelta(minutes=60)
    db.commit()
    db.close()
    
    user_token = create_access_token({"sub": "cidadao@exemplo.com"})
    with pytest.raises(Exception) as excinfo:
        get_current_user_optional(token=user_token, db=TestingSessionLocal())
    assert "banida" in str(excinfo.value)
    
    # Unban user
    db = TestingSessionLocal()
    user = db.query(UserModel).filter_by(email="cidadao@exemplo.com").first()
    user.banned_until = None
    db.commit()
    db.close()



def test_jwt_default_expire():
    from app.security.jwt import create_access_token
    token = create_access_token({"sub": "test@test.com"})
    assert token is not None


def test_verify_password_exception():
    from app.security.password import verify_password
    assert verify_password("plain", None) is False


def test_audit_logs_logout_and_failures():
    # 1. Login to get token
    login_response = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "senha123"}
    )
    assert login_response.status_code == 200
    user_token = login_response.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 2. Call logout
    logout_resp = client.post("/api/auth/logout", headers=user_headers)
    assert logout_resp.status_code == 200

    # 3. Call login with failure (wrong password)
    fail_login_resp = client.post(
        "/api/auth/login",
        data={"username": "cidadao@exemplo.com", "password": "wrongpassword"}
    )
    assert fail_login_resp.status_code == 401

    # 4. Login as admin
    admin_login = client.post(
        "/api/auth/login",
        data={"username": "admin@riou.com", "password": "admin123"}
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 5. Retrieve audit logs
    audit_resp = client.get("/api/admin/audit-logs", headers=admin_headers)
    assert audit_resp.status_code == 200
    logs = audit_resp.json()

    # Verify that LOGIN, LOGOUT, and LOGIN_FAILURE actions are in the logs
    actions = [log["action"] for log in logs]
    assert "LOGIN" in actions
    assert "LOGOUT" in actions
    assert "LOGIN_FAILURE" in actions

    # Verify that the descriptions are present
    login_failure_log = next(log for log in logs if log["action"] == "LOGIN_FAILURE")
    assert "Tentativa de login falhou" in login_failure_log["details"]

    logout_log = next(log for log in logs if log["action"] == "LOGOUT")
    assert "Logout realizado com sucesso" in logout_log["details"]


def test_ping_success():
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ping_failure():
    # Define an error-throwing db session dependency
    def override_get_db_error():
        class BadSession:
            def execute(self, *args, **kwargs):
                raise Exception("Simulated DB connection failure")
        yield BadSession()

    app.dependency_overrides[get_db] = override_get_db_error
    try:
        response = client.get("/ping")
        assert response.status_code == 500
        assert "detail" in response.json()
    finally:
        # Restore normal get_db override
        app.dependency_overrides[get_db] = override_get_db






