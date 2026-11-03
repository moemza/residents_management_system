import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import AdminSession, AdminUser

SESSION_COOKIE = "residents_admin_session"
SESSION_ABSOLUTE_SECONDS = 8 * 60 * 60
SESSION_IDLE_SECONDS = 30 * 60
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DUMMY_SALT = b"residents-admin-login-dummy"


def cookie_secure() -> bool:
    """Require secure cookies by default; allow an explicit local-HTTP override."""
    return os.environ.get("RESIDENTS_COOKIE_SECURE", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _password_digest(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=32,
    )


def hash_password(password: str) -> str:
    """Return a salted scrypt password hash for operator provisioning."""
    if not 12 <= len(password) <= 1024:
        raise ValueError("Admin passwords must be 12 to 1024 characters")
    salt = secrets.token_bytes(16)
    digest = _password_digest(password, salt)
    return "scrypt${}${}${}${}${}".format(
        _SCRYPT_N,
        _SCRYPT_R,
        _SCRYPT_P,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str | None) -> bool:
    """Verify a stored scrypt password hash, doing comparable work for unknown users."""
    if not encoded:
        _password_digest(password, _DUMMY_SALT)
        return False
    try:
        algorithm, n, r, p, salt_value, digest_value = encoded.split("$")
        if (
            algorithm != "scrypt"
            or int(n) != _SCRYPT_N
            or int(r) != _SCRYPT_R
            or int(p) != _SCRYPT_P
        ):
            raise ValueError("Unsupported password hash")
        salt = base64.urlsafe_b64decode(salt_value.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_value.encode("ascii"))
        if len(salt) != 16 or len(expected) != 32:
            raise ValueError("Invalid password hash")
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=len(expected),
        )
    except (ValueError, TypeError, UnicodeError, OverflowError):
        _password_digest(password, _DUMMY_SALT)
        return False
    return hmac.compare_digest(actual, expected)


def create_session(db: Session, user: AdminUser) -> tuple[str, str]:
    """Create an opaque, hashed server-side session and return its cookie/CSRF secrets."""
    now = _utcnow()
    db.query(AdminSession).filter(
        (AdminSession.expires_at <= now)
        | (
            AdminSession.last_activity_at
            <= now - timedelta(seconds=SESSION_IDLE_SECONDS)
        )
    ).delete(synchronize_session=False)
    session_token = secrets.token_urlsafe(32)
    db.add(
        AdminSession(
            user_id=user.id,
            token_hash=hashlib.sha256(session_token.encode("ascii")).hexdigest(),
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(seconds=SESSION_ABSOLUTE_SECONDS),
        )
    )
    db.commit()
    return session_token, csrf_token_for(session_token)


def csrf_token_for(session_token: str) -> str:
    return hmac.new(
        session_token.encode("ascii"), b"residents-admin-csrf", hashlib.sha256
    ).hexdigest()


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_ABSOLUTE_SECONDS,
        httponly=True,
        secure=cookie_secure(),
        samesite="strict",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        httponly=True,
        secure=cookie_secure(),
        samesite="strict",
        path="/",
    )


def get_session_user(
    request: Request,
    db: Session,
    *,
    touch: bool = True,
) -> tuple[AdminUser | None, AdminSession | None]:
    """Validate session expiry and activity, optionally extending its idle window."""
    token = request.cookies.get(SESSION_COOKIE, "")
    if not token or len(token) > 256 or not token.isascii():
        return None, None

    token_hash = hashlib.sha256(token.encode("ascii", errors="ignore")).hexdigest()
    session = db.query(AdminSession).filter(AdminSession.token_hash == token_hash).first()
    if session is None:
        return None, None

    now = _utcnow()
    created_at = _as_utc(session.created_at)
    last_activity_at = _as_utc(session.last_activity_at)
    expires_at = _as_utc(session.expires_at)
    if (
        now >= expires_at
        or now - created_at >= timedelta(seconds=SESSION_ABSOLUTE_SECONDS)
        or now - last_activity_at >= timedelta(seconds=SESSION_IDLE_SECONDS)
    ):
        db.delete(session)
        db.commit()
        return None, None

    user = db.query(AdminUser).filter(AdminUser.id == session.user_id).first()
    if user is None or not user.is_active:
        db.delete(session)
        db.commit()
        return None, None

    if touch:
        session.last_activity_at = now
        db.commit()
    return user, session


def require_admin(request: Request, db: Session = Depends(get_db)) -> AdminUser:
    user, session = get_session_user(request, db)
    if user is None or session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator authentication required",
        )
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        supplied = request.headers.get("x-csrf-token", "")
        token = request.cookies.get(SESSION_COOKIE, "")
        expected = csrf_token_for(token)
        if not supplied or not hmac.compare_digest(supplied, expected):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed",
            )

    request.state.admin_username = user.username
    return user
