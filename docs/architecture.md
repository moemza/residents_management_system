# Architecture

## Overview

The system follows a client-server architecture with a React single-page
application and a FastAPI JSON API backed by SQLite.

```
┌─────────────────────────────┐        HTTP/JSON        ┌──────────────────────────────┐
│        React SPA            │ ──────────────────────► │      FastAPI Backend         │
│  Vite dev: 5173             │ ◄────────────────────── │      uvicorn, port 8000      │
│  Production: served by API  │                         └──────────────┬───────────────┘
└─────────────────────────────┘                                        │ SQLAlchemy ORM
                                                                       ▼
                                                        ┌──────────────────────────────┐
                                                        │        SQLite Database       │
                                                        │  /data/residents.db (Docker) │
                                                        │  database/residents.db (dev) │
                                                        └──────────────────────────────┘
```

In development, Vite serves the frontend and proxies `/api` to the API. In
production, the backend serves the built `frontend/dist` directory and the API
from the same origin.

---

## Backend (`app/`)

| File | Responsibility |
|---|---|
| `main.py` | App instance, lifespan integrity check, CORS, request-size limit, rate limiting, request IDs, security/cache headers, health endpoint, SPA serving |
| `api_routes.py` | Residents CRUD, search, pagination, validation, non-PII audit trail, auth-protected router |
| `auth.py` | Scrypt password verification, opaque sessions, CSRF, and admin authorization |
| `models.py` | SQLAlchemy ORM models, audit events, and indexes |
| `database.py` | Engine, sessions, SQLite pragmas, index creation, integrity checks, consistent backups |
| `migrations.py` | Legacy HTML-entity reporting and normalisation |
| `rate_limit.py` | In-process sliding-window per-client limiter |
| `schemas.py` | Pydantic request models, response contracts, and validation limits |
| `qualifications.py` | Static qualification reference data and field-to-name mapping |
| `villages.py` | Static village list |

### Request lifecycle

1. React sends an HTTP request via Axios to `/api/...`.
2. Security/cache headers are applied to the response by outer middleware.
3. A request ID is reused from a well-formed `X-Request-ID` header or generated
   and attached to `request.state` and the response.
4. The per-client rate limiter rejects excess `/api/*` requests with `429` and
   `Retry-After`.
5. Middleware rejects oversized request bodies with `413`.
6. `require_admin` validates the cookie session, active account, admin role, and CSRF header for state-changing requests.
7. FastAPI routes the request to the matching handler in `api_routes.py`.
8. Pydantic trims values, enforces length and row limits, rejects markup and
   invalid dates, and normalises blank optional values to `null`.
9. The handler uses a SQLAlchemy `Session` injected through `Depends(get_db)`.
10. On write operations, `backup_database()` creates a consistent, verified
    pre-write snapshot when backups are enabled.
11. The handler writes a non-PII audit event, commits, rolls back on error, and
    returns an explicit response model.
12. List, search, and audit responses include `X-Total-Count` for pagination.

On startup, the lifespan handler verifies the database with `PRAGMA quick_check`
before creating missing tables and indexes. A corrupt database prevents startup
rather than serving unverified data.

### Database

- SQLite file at `database/residents.db` by default; configurable through
  `RESIDENTS_DB_PATH`.
- Tables are created on startup with `Base.metadata.create_all()`. Missing
  indexes are added with `CREATE INDEX IF NOT EXISTS`. This is not a general
  schema-migration system and does not alter existing columns.
- Every connection enables foreign keys, a 5-second busy timeout, and WAL
  journal mode.
- Backups are stored in `database/backups/` by default; configurable through
  `RESIDENTS_BACKUP_DIR`. The newest 10 are retained by default; retention is
  configurable with `RESIDENTS_BACKUP_RETENTION`.
- Backups use SQLite's online backup API and `PRAGMA quick_check`, and are taken
  before writes. Backup failures are best-effort by default; set
  `RESIDENTS_BACKUP_REQUIRED=true` to abort writes with `503` when an enabled
  backup fails.
- Startup runs `PRAGMA quick_check` when `RESIDENTS_DB_INTEGRITY_CHECK=true` and
  refuses to start on corruption.
- Backups are still local, unencrypted, and not a substitute for an off-host
  recovery process. See [operations.md](operations.md).

### Data model

```
Resident
  ├── id, first_name, last_name, dob, gender, village
  ├── cellphone_no, cellphone_no2, email
  ├── qualifications  →  Qualification (institution, name, type, level, year)
  ├── experiences     →  Experience (company, position, years)
  └── skills          →  Skill (name)

AuditEvent
  └── id, created_at, action, resident_id, actor, request_id, detail
```

All child records use `cascade="all, delete-orphan"`, so deleting a resident
removes all related records. Foreign keys are enforced at the database level.
Child relationships are eager-loaded with `selectinload` for list and search to
avoid N+1 queries.

`AuditEvent` deliberately has no foreign key to `Resident`, so audit rows survive
deletion and contain no resident values. The `detail` column records changed
contact field names only.

Identity fields (`first_name`, `last_name`, `dob`, `gender`, `village`) are
immutable through `PUT`; contact fields and child rows can be replaced.

---

## Frontend (`frontend/src/`)

| Path | Responsibility |
|---|---|
| `api/residents.js` | Axios client, session cookies, CSRF header, 401 handling, paginated list/search helpers |
| `api/errors.js` | Normalises FastAPI string and array error details |
| `api/pagination.js` | Pure page-range and page-clamping helpers |
| `auth.js` | In-memory CSRF token helper |
| `components/AppNavigation.jsx` | Responsive navigation and server logout |
| `pages/Home.jsx` | Responsive resident-management dashboard |
| `pages/Login.jsx` | Accessible administrator username/password entry |
| `pages/Residents.jsx` | Paginated resident browser |
| `pages/AddResident.jsx` | Create form with client-side validation and focus handling |
| `pages/EditResident.jsx` | Edit form; identity fields are read-only |
| `pages/ViewResident.jsx` | Read-only detail view and confirmed delete with focus restoration |
| `pages/SearchResident.jsx` | Search form, result list, and server-side pagination |
| `components/EducationSection.jsx` | Dynamic add/remove education rows |
| `components/ExperienceSection.jsx` | Dynamic add/remove experience rows |
| `components/SkillsSection.jsx` | Dynamic add/remove skill rows |
| `components/Toast.jsx` | Auto-dismissing, accessible live notification |
| `components/ErrorBoundary.jsx` | Last-resort render-error fallback |
| `hooks/useToast.js` | Toast state management |
| `hooks/useDocumentTitle.js` | Per-page browser titles |
| `App.jsx` | Routes, auth-status check, auth guard, skip link/main landmark, global toast |
| `main.jsx` | React root, BrowserRouter, Bootstrap CSS import |

### Authentication flow

1. `App.jsx` calls `GET /api/auth/status`; the server validates the HTTP-only
   cookie and returns a session-bound CSRF token for authenticated admins.
2. The login form sends credentials to `POST /api/auth/login`. The backend
   verifies the scrypt password hash, role, and account status, stores a hash
   of a random session token in SQLite, and sets an HTTP-only cookie.
3. The React client keeps only the CSRF token in memory and sends it on writes.
4. Protected API routes validate the session and admin role on every request.
   The production SPA server also protects direct page loads; only `/login` is
   public. `/health` and `/api/auth/status` remain public and expose no resident
   data.
5. Sessions expire after 30 minutes idle or 8 hours absolute. Logout revokes the
   database session; deactivating an account revokes its active sessions.
6. Write audit events record the admin username, request ID, and non-PII action
   details; read access is not currently audited.

### Data flow (create resident example)

1. User fills the form in `AddResident.jsx`.
2. Client-side validation shows inline errors using Bootstrap `is-invalid`.
3. `createResident(payload)` sends `POST /api/residents`.
4. On success, the app navigates to `/residents` and shows a toast.
5. On error, `getApiErrorMessage` converts FastAPI details into readable text
   and the first invalid field receives focus on client-side failures.

### Routing

| Path | Component |
|---|---|
| `/login` | `Login` |
| `/` | `Home` |
| `/residents` | `Residents` |
| `/add-resident` | `AddResident` |
| `/edit-resident/:id` | `EditResident` |
| `/view-resident/:id` | `ViewResident` |
| `/search` | `SearchResident` |

The backend SPA fallback serves `index.html` for unknown non-API paths so these
client-side routes work on a full page load. `App.jsx` provides a skip link, a
`<main>` landmark, and moves focus to the new page after client-side navigation.
An `ErrorBoundary` replaces a blank render failure with a recoverable message.

---

## Security and privacy

- **Authentication** — operator-provisioned accounts, scrypt password hashes,
  server-side sessions, admin role enforcement, CSRF validation, logout, and
  8-hour absolute / 30-minute idle expiry. No public registration.
- **Page and data protection** — backend guards direct page loads and every
  resident/reference/audit API call; only the login shell, health, and auth
  status are public.
- **Audit trail** — non-PII create/update/delete events with admin username,
  request ID, resident ID, and changed field names. Read access is not audited.
- **Rate limiting** — in-process sliding window per client (default 300/minute
  plus a 10/minute login limit); not distributed, use a proxy/platform limit.
- **Request correlation** — validated or generated request IDs are returned and
  included in audit events.
- **Data handling** — strict validation, raw text storage with React escaping,
  restrictive CSP, security headers, and no-store API responses.
- **Storage** — SQLite integrity checks, foreign-key constraints, and verified
  pre-write backups; local database/backups are not application-encrypted.

Remaining operational and accessibility risks are tracked in
[gap-register.md](gap-register.md).

## Tests

| File | Covers |
|---|---|
| `conftest.py` | Temporary isolated DB, disabled backups, synthetic base payload |
| `test_api_contract.py` | Explicit OpenAPI response models, pagination parameters, audit schema |
| `test_audit.py` | Non-PII audit events, filters, pagination, delete survival, auth |
| `test_auth.py` | Admin login, bad credentials, role denial, CSRF, direct API/page denial, logout, and idle/absolute expiry |
| `test_backup_behavior.py` | Best-effort vs required pre-write backup failure |
| `test_configuration.py` | Test isolation, CORS parsing |
| `test_database_backup.py` | Backup disablement, collision-safe names, configurable retention |
| `test_database_integrity.py` | Startup integrity verification, FK pragma, indexes, orphan rejection, backup integrity |
| `test_edge_cases.py` | Boundary values, malformed bodies, markup rejection, search edge cases |
| `test_form_submission.py` | Full resident CRUD |
| `test_health_and_headers.py` | Health, security headers, request-size limit, 404, OpenAPI |
| `test_health.py` | Docs availability and schema title |
| `test_identity_and_limits.py` | Identity immutability, length/row limits, blank child rows |
| `test_integration_add_resident.py` | Add Resident user stories US-01–US-07 |
| `test_integration_edit_resident.py` | Edit Resident user stories US-ER-01–US-ER-06 |
| `test_integration_search_resident.py` | Search Resident user stories US-SR-01–US-SR-08 |
| `test_migrations.py` | Dry-run, apply, backup, idempotency, CLI safety |
| `test_observability.py` | Request IDs, cache headers, CORS exposure, rate limiting, limiter bounds |
| `test_pagination.py` | Limit/offset, totals, invalid bounds |
| `test_qualifications.py` | Qualifications endpoint |
| `test_search_qualification.py` | Field-to-name mapping and literal LIKE wildcards |
| `test_validation.py` | Required fields, email/date format, empty search |
| `test_villages.py` | Villages endpoint |

Frontend unit tests live in `frontend/tests/` and use Node's built-in test
runner. They cover error normalisation, in-memory CSRF token handling, and pagination helpers.

`conftest.py` creates a temporary directory, points `RESIDENTS_DB_PATH` and
`RESIDENTS_BACKUP_DIR` inside it, and sets `RESIDENTS_BACKUP_ENABLED=false`,
`RESIDENTS_RATE_LIMIT_PER_MINUTE=0`, and `RESIDENTS_DB_INTEGRITY_CHECK=false`
before importing the application. Tests use synthetic data only and must not be
run against a database containing real resident data.

### Commands

```bash
# Full backend suite
.venv/bin/python -m pytest tests/ -v

# Coverage
.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing

# Frontend tests, lint, build
cd frontend
npm test
npm run lint
npm run build
```

---

## Reference data

- Villages: edit `VILLAGES` in `app/villages.py`.
- Qualification types, levels, fields, and names: edit the constants in
  `app/qualifications.py`.

These are static lists served by the API; no database migration is needed when
they change.
