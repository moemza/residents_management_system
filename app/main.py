import hashlib
import logging
import os
import pathlib
import traceback
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import auth, database
from .api_routes import router as api_router
from .auth import get_session_user, require_admin
from .database import BASE_DIR, engine, get_db
from .models import AdminSession, AdminUser
from .rate_limit import limiter
from .schemas import AdminLoginIn, AdminLoginOut, AuthStatusOut, ErrorOut, HealthOut

logger = logging.getLogger(__name__)

DEFAULT_FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
DEFAULT_RATE_LIMIT_PER_MINUTE = 300


def _cors_origins() -> list[str]:
    """Return configured browser origins, defaulting to the local Vite app."""
    configured = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    if "*" in origins:
        raise ValueError(
            "CORS_ORIGINS must list explicit trusted origins when credentials are enabled"
        )
    return origins


def _frontend_dir() -> pathlib.Path:
    """Return the configured built-frontend directory."""
    configured = os.environ.get("RESIDENTS_FRONTEND_DIR", "").strip()
    return pathlib.Path(configured).expanduser() if configured else DEFAULT_FRONTEND_DIR


def _max_request_bytes() -> int:
    """Return the configured maximum request body size."""
    try:
        return max(1, int(os.environ.get("RESIDENTS_MAX_REQUEST_BYTES", "1000000")))
    except ValueError:
        return 1_000_000


def _hsts_enabled() -> bool:
    return os.environ.get("RESIDENTS_HSTS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _rate_limit_per_minute() -> int:
    """Return the per-client API request limit; zero disables limiting."""
    try:
        return max(
            0,
            int(
                os.environ.get(
                    "RESIDENTS_RATE_LIMIT_PER_MINUTE",
                    str(DEFAULT_RATE_LIMIT_PER_MINUTE),
                )
            ),
        )
    except ValueError:
        return DEFAULT_RATE_LIMIT_PER_MINUTE


def _trust_proxy_headers() -> bool:
    return os.environ.get("RESIDENTS_TRUST_PROXY", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _client_key(request: Request) -> str:
    """Identify the caller without storing it.

    ``X-Forwarded-For`` is only used when the deployment explicitly opts in, so
    a direct client cannot spoof its rate-limit key by default.
    """
    if _trust_proxy_headers():
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",", 1)[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


def _request_id(request: Request) -> str:
    """Reuse a well-formed caller request ID or generate a new one.

    Only ASCII is accepted: response headers are ISO-8859-1, so a caller value
    containing other characters would fail when the response is serialised.
    """
    supplied = request.headers.get("x-request-id", "").strip()
    if (
        supplied
        and len(supplied) <= 64
        and all(
            character.isascii()
            and (character.isalnum() or character in "-_.")
            for character in supplied
        )
    ):
        return supplied
    return uuid.uuid4().hex


def _content_security_policy() -> str:
    """Build a conservative CSP for the bundled single-page application."""
    connect_sources = " ".join(["'self'", *_cors_origins()])
    return (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        f"connect-src {connect_sources}; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Check integrity before create_tables() so a corrupt file fails with a
    # clear message instead of a low-level SQLite error while creating indexes.
    if database.DB_INTEGRITY_CHECK and not database.verify_database_integrity():
        logger.critical(
            "Database integrity check failed for %s; refusing to start",
            database.DB_PATH,
        )
        raise RuntimeError("Database integrity check failed")
    database.create_tables()
    yield


app = FastAPI(title="Residents Management API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Browser clients on a different origin need this exposed to read totals.
    expose_headers=["X-Total-Count"],
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject oversized request bodies before they reach route handlers."""
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            size = int(content_length)
        except ValueError:
            return JSONResponse(
                status_code=400, content={"detail": "Invalid Content-Length header"}
            )
        if size > _max_request_bytes():
            return JSONResponse(
                status_code=413,
                content={"detail": "Request body is too large"},
            )
    return await call_next(request)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """Apply a per-client sliding-window limit to API routes."""
    limit = _rate_limit_per_minute()
    if limit and request.url.path.startswith("/api/"):
        allowed, retry_after = limiter.check(_client_key(request), limit)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers={"Retry-After": str(retry_after)},
            )
    if request.url.path == "/api/auth/login":
        allowed, retry_after = limiter.check(f"login:{_client_key(request)}", 10)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many login attempts"},
                headers={"Retry-After": str(retry_after)},
            )
    return await call_next(request)


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Attach a correlation ID to the request and the response."""
    request.state.request_id = _request_id(request)
    response = await call_next(request)
    response.headers.setdefault("X-Request-ID", request.state.request_id)
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Attach baseline browser-security headers to every response."""
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy", "camera=(), geolocation=(), microphone=()"
    )
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
    response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")
    # Resident data and health details must not be stored by browsers or
    # intermediary caches.
    if request.url.path.startswith("/api/") or request.url.path == "/health":
        response.headers.setdefault("Cache-Control", "no-store")
    # Swagger UI and ReDoc load their own assets and inline bootstrap scripts.
    # Exempt the documentation pages so the strict application CSP does not
    # break them.
    if request.url.path not in {
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
        "/openapi.json",
    }:
        response.headers.setdefault(
            "Content-Security-Policy", _content_security_policy()
        )
    if _hsts_enabled():
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
    return response


@app.get("/api/auth/status", response_model=AuthStatusOut, tags=["auth"])
def auth_status(request: Request, response: Response, db: Session = Depends(get_db)):
    """Report server-side admin-session state without exposing account details."""
    user, session = get_session_user(request, db)
    if user is not None and session is not None and user.role == "admin":
        return {
            "auth_required": True,
            "authenticated": True,
            "csrf_token": auth.csrf_token_for(
                request.cookies.get(auth.SESSION_COOKIE, "")
            ),
        }
    if session is not None:
        db.delete(session)
        db.commit()
    auth.clear_session_cookie(response)
    return {"auth_required": True, "authenticated": False, "csrf_token": None}


@app.post("/api/auth/login", response_model=AdminLoginOut, tags=["auth"])
def admin_login(
    credentials: AdminLoginIn,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate an operator-provisioned administrator and issue a session."""
    origin = request.headers.get("origin")
    if origin and origin not in _cors_origins():
        raise HTTPException(status_code=403, detail="Origin not allowed")

    username = credentials.username.strip().casefold()
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if user is None or not auth.verify_password(
        credentials.password, user.password_hash if user else None
    ) or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")

    token, csrf_token = auth.create_session(db, user)
    auth.set_session_cookie(response, token)
    return {"authenticated": True, "csrf_token": csrf_token}


@app.post("/api/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["auth"])
def admin_logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    user: AdminUser = Depends(require_admin),
):
    """Revoke this server-side session and expire its browser cookie."""
    del user
    token = request.cookies.get(auth.SESSION_COOKIE, "")
    token_hash = hashlib.sha256(token.encode("ascii", errors="ignore")).hexdigest()
    session = db.query(AdminSession).filter(AdminSession.token_hash == token_hash).first()
    if session is not None:
        db.delete(session)
        db.commit()
    auth.clear_session_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return None


@app.get(
    "/health",
    response_model=HealthOut,
    responses={503: {"model": HealthOut}},
    tags=["health"],
)
def health():
    """Report process and database health without exposing resident data."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:  # pragma: no cover - depends on an unavailable database
        logger.exception("Health check failed")
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable"},
        )
    return {"status": "ok", "database": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Do not log the query string or the exception message: both can contain
    # resident data. The stack frames are sufficient for diagnosis.
    stack = "".join(traceback.format_tb(exc.__traceback__))
    logger.error(
        "Unhandled error on %s (%s)\n%s",
        request.url.path,
        type(exc).__name__,
        stack,
    )
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred. Please try again."})


app.include_router(api_router, prefix="/api")


# Serve the built React application when it exists. API routes are registered
# first, so they take precedence. Unknown paths return index.html so client-side
# routes such as /edit-resident/1 work on a full page load.
_frontend = _frontend_dir()
if _frontend.is_dir():
    assets_dir = _frontend / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(
    full_path: str,
    request: Request,
    db: Session = Depends(get_db),
):
    # Never mask missing API or health routes with the SPA shell.
    if full_path == "health" or full_path.startswith("api/"):
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    if full_path != "login":
        user, session = get_session_user(request, db)
        if user is None or session is None or user.role != "admin":
            if session is not None:
                db.delete(session)
                db.commit()
            return RedirectResponse("/login", status_code=303)
    if not _frontend.is_dir():
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    root = _frontend.resolve()
    candidate = (root / full_path).resolve()
    if candidate.is_file() and candidate.is_relative_to(root):
        return FileResponse(candidate)
    index = root / "index.html"
    if not index.is_file():
        return JSONResponse(status_code=404, content={"detail": "Not Found"})
    return FileResponse(index)
