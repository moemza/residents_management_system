from datetime import datetime, timedelta, timezone

import pytest

from app import auth
from app.auth import hash_password
from app.models import AdminSession, AdminUser
from .conftest import RESIDENT_PAYLOAD, TestingSession


ADMIN_CREDENTIALS = {
    "username": "test-admin",
    "password": "test-only-password-123",
}


def _create_user(username, password, role="admin"):
    with TestingSession() as db:
        user = AdminUser(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


def test_unauthenticated_api_requests_are_denied_and_public_probes_remain_open(anonymous_client):
    for path in ("/api/residents", "/api/villages", "/api/audit", "/api/auth/verify"):
        assert anonymous_client.get(path).status_code == 401
    assert anonymous_client.post("/api/residents", json=RESIDENT_PAYLOAD).status_code == 401
    page = anonymous_client.get("/residents", follow_redirects=False)
    assert page.status_code == 303
    assert page.headers["location"] == "/login"
    status = anonymous_client.get("/api/auth/status")
    assert status.status_code == 200
    assert status.json() == {
        "auth_required": True,
        "authenticated": False,
        "csrf_token": None,
    }
    assert anonymous_client.get("/health").status_code == 200
    assert anonymous_client.post("/api/auth/register", json={}).status_code == 405


def test_admin_can_load_a_protected_page_directly(client):
    response = client.get("/residents", follow_redirects=False)
    assert response.status_code in {200, 404}
    assert response.status_code != 303


def test_invalid_credentials_do_not_create_a_session(anonymous_client):
    response = anonymous_client.post(
        "/api/auth/login",
        json={"username": ADMIN_CREDENTIALS["username"], "password": "incorrect-password"},
    )
    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert anonymous_client.get("/api/residents").status_code == 401


def test_valid_admin_login_issues_http_only_session_and_csrf_protection(anonymous_client):
    response = anonymous_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)
    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert len(response.json()["csrf_token"]) >= 32
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=strict" in cookie
    assert "residents_admin_session=" in cookie

    assert anonymous_client.get("/api/residents").status_code == 200
    denied_write = anonymous_client.post("/api/residents", json=RESIDENT_PAYLOAD)
    assert denied_write.status_code == 403
    created = anonymous_client.post(
        "/api/residents",
        json=RESIDENT_PAYLOAD,
        headers={"X-CSRF-Token": response.json()["csrf_token"]},
    )
    assert created.status_code == 201


def test_non_admin_cannot_sign_in_or_access_protected_api(anonymous_client):
    user_id = _create_user("staff-user", "another-test-password-123", role="staff")
    response = anonymous_client.post(
        "/api/auth/login",
        json={"username": "staff-user", "password": "another-test-password-123"},
    )
    assert response.status_code == 403
    assert anonymous_client.get("/api/residents").status_code == 401

    with TestingSession() as db:
        user = db.get(AdminUser, user_id)
        token, _ = auth.create_session(db, user)
    anonymous_client.cookies.set(auth.SESSION_COOKIE, token)
    assert anonymous_client.get("/api/residents").status_code == 403


def test_logout_revokes_the_server_session(anonymous_client):
    response = anonymous_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)
    csrf_token = response.json()["csrf_token"]
    logout = anonymous_client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout.status_code == 204
    assert anonymous_client.get("/api/auth/status").json()["authenticated"] is False
    assert anonymous_client.get("/api/residents").status_code == 401


@pytest.mark.parametrize("expired_field", ["last_activity_at", "expires_at"])
def test_expired_sessions_are_rejected(anonymous_client, expired_field):
    response = anonymous_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)
    with TestingSession() as db:
        session = db.query(AdminSession).one()
        setattr(
            session,
            expired_field,
            datetime.now(timezone.utc) - timedelta(hours=9),
        )
        db.commit()
    assert anonymous_client.get("/api/residents").status_code == 401


def test_session_touch_does_not_extend_absolute_expiry(anonymous_client):
    response = anonymous_client.post("/api/auth/login", json=ADMIN_CREDENTIALS)
    assert response.status_code == 200
    with TestingSession() as db:
        session = db.query(AdminSession).one()
        session.created_at = datetime.now(timezone.utc) - timedelta(hours=9)
        session.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session.last_activity_at = datetime.now(timezone.utc)
        db.commit()
    assert anonymous_client.get("/api/residents").status_code == 401


def test_disabling_account_revokes_its_existing_session(client):
    with TestingSession() as db:
        user = db.query(AdminUser).filter_by(username="test-admin").one()
        user.is_active = False
        db.commit()
    assert client.get("/api/residents").status_code == 401


def test_password_hashing_requires_a_strong_operator_password():
    with pytest.raises(ValueError):
        hash_password("short")
    encoded = hash_password("synthetic-test-password")
    assert auth.verify_password("synthetic-test-password", encoded)
    assert not auth.verify_password("wrong-test-password", encoded)
