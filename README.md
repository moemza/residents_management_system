# Residents Management System

A web application for managing resident records including personal details,
qualifications, work experience, and skills.

The backend is a **FastAPI (Python)** JSON REST API backed by **SQLite** via
**SQLAlchemy**. The frontend is a **React (Vite)** single-page application using
**Bootstrap 5**.

---

## Features

- Create, view, edit, and delete residents
- Manage qualifications, work experience, and skills per resident
- Browse residents in a paginated list
- Search by name, village, qualification field/name, or skill
- Server-side validation with documented length limits and markup rejection
- Operator-provisioned administrator accounts with expiring server-side sessions
- Pagination for resident listings and search results (`limit` / `offset`)
- Non-PII write audit trail (`GET /api/audit`)
- In-process per-client rate limiting and request correlation IDs
- Consistent SQLite backups before writes, with integrity checks and retention
- Startup database integrity verification; opt-in fail-closed backups
- Health endpoint and baseline browser-security headers
- Production static serving of the built React application
- React/JSX output escaping; no `dangerouslySetInnerHTML`
- Inline toast notifications — no `alert()` / `confirm()` / `prompt()`
- Global render error boundary, skip link, page titles, and accessible forms
- Backend and frontend automated tests, linting, dependency audit, and CI

Known limitations and remaining operational decisions are recorded in
[docs/gap-register.md](docs/gap-register.md). Deployment and recovery guidance is
in [docs/operations.md](docs/operations.md).

---

## Project Structure

```
├── app/
│   ├── api_routes.py      # REST endpoints, validation, pagination, search, audit
│   ├── auth.py            # Scrypt passwords, sessions, CSRF, admin authorization
│   ├── database.py        # Engine, sessions, pragmas, indexes, backups
│   ├── main.py            # App wiring, rate limit, headers, health, SPA serving
│   ├── migrations.py      # Legacy HTML-entity normalisation utility
│   ├── models.py          # Resident, audit, admin, and session ORM models
│   ├── rate_limit.py      # In-process sliding-window rate limiter
│   ├── schemas.py         # Pydantic request/response contracts and limits
│   ├── qualifications.py  # Qualification reference data
│   └── villages.py        # Village reference data
├── frontend/
│   ├── src/
│   │   ├── api/           # Axios client, pagination, error helpers
│   │   ├── components/    # Navigation, Toast, ErrorBoundary, form sections
│   │   ├── hooks/         # useToast, useDocumentTitle
│   │   ├── pages/         # Home, Residents, Add/Edit/View/Search, Login
│   │   ├── App.jsx        # Routes, auth guard, landmarks, global toast
│   │   ├── auth.js        # In-memory CSRF token helper
│   │   └── main.jsx       # Entry point
│   ├── tests/             # Node built-in unit tests
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json  # Tracked for reproducible npm ci installs
│   └── vite.config.js     # Dev/preview proxy for /api
├── database/              # Local SQLite database and backups (gitignored)
├── docs/
│   ├── api.md             # API reference
│   ├── architecture.md    # System architecture
│   ├── configuration.md   # Environment variables and test isolation
│   ├── operations.md      # Deployment, backup, restore, migration, monitoring
│   ├── gap-register.md    # Findings, fixes, and remaining risks
│   ├── changes/           # Dated change records
│   └── user-stories/      # Feature user stories
├── scripts/
│   ├── migrate_unescape.py
│   └── provision_admin.py
├── tests/                 # Isolated pytest suite (synthetic data only)
├── .github/workflows/ci.yml
├── .dockerignore
├── Dockerfile             # Multi-stage frontend build + non-root API runtime
├── docker-compose.example.yml
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Runtime + test dependencies
└── README.md
```

---

## Requirements

- Python **3.12+** (tested with Python 3.12)
- Node.js **20.19+ or 22+** (CI uses Node 22)
- SQLite is provided by Python's standard library

---

## Backend Setup

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install runtime + development dependencies
pip install -r requirements-dev.txt

# Start the API server
uvicorn app.main:app --reload
```

- API: [http://localhost:8000](http://localhost:8000)
- Health: [http://localhost:8000/health](http://localhost:8000/health)
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

The database and tables are created automatically on first startup. Existing
databases receive missing indexes on startup; this is not a general schema
migration system.

For production, install only `requirements.txt`.

---

## Frontend Setup

```bash
cd frontend
npm ci
npm run dev
```

React app: [http://localhost:5173](http://localhost:5173)

Vite proxies `/api` to `http://localhost:8000`, so the default frontend API URL
is same-origin. Set `VITE_API_BASE_URL` only for a split deployment.

To run the production build locally through FastAPI:

```bash
cd frontend
npm run build
cd ..
uvicorn app.main:app
# Open http://localhost:8000
```

The backend serves `frontend/dist` when it exists. Override the directory with
`RESIDENTS_FRONTEND_DIR`.

---

## Authentication

All resident APIs and protected UI routes require an administrator session.
Create accounts only through the operator CLI; there is no public registration
endpoint. For local HTTP development, provision an account and run:

```bash
export RESIDENTS_COOKIE_SECURE=false
.venv/bin/python -m scripts.provision_admin create admin
uvicorn app.main:app
```

The CLI prompts for a password of at least 12 characters and stores a salted
scrypt hash. `RESIDENTS_COOKIE_SECURE` defaults to `true` and should remain
enabled behind HTTPS; disable it only for local HTTP development. Sessions are
HTTP-only, SameSite Strict, CSRF-protected, expire after 30 minutes idle or 8
hours absolute, and are revoked on logout. `/health` and `/api/auth/status` are
public and expose no resident data. See
[docs/configuration.md](docs/configuration.md) and
[docs/operations.md](docs/operations.md) for provisioning and deployment.

---

## Running Tests and Checks

Backend tests use a temporary SQLite database created by `tests/conftest.py` and
run with database backups disabled. They use synthetic data only and must not be
run against a database containing real resident data.

```bash
# Backend suite
.venv/bin/python -m pytest tests/ -q

# Coverage
.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing -q

# Frontend unit tests, lint, production build, and dependency audit
cd frontend
npm ci
npm test
npm run lint
npm run build
npm audit
```

`npm audit` currently reports **0 vulnerabilities**. Re-run it after any
dependency change; the frontend lockfile is tracked so `npm ci` installs the
reviewed graph.

Run a specific backend test file:

```bash
.venv/bin/python -m pytest tests/test_integration_search_resident.py -v
```

Run only integration tests:

```bash
.venv/bin/python -m pytest tests/ -v -k "integration"
```

The latest verified results are recorded in the pull request and
[docs/gap-register.md](docs/gap-register.md); do not infer passing checks from
source changes alone.

CI runs the same checks on push and pull request; see
`.github/workflows/ci.yml`.

---

## Configuration

Runtime paths, authentication, CORS, request limits, security headers, backup
behaviour, and the frontend API URL are configurable through environment
variables. See [docs/configuration.md](docs/configuration.md) for defaults and
examples.

Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `RESIDENTS_DB_PATH` | `<repo>/database/residents.db` | SQLite database file |
| `RESIDENTS_BACKUP_DIR` | `<repo>/database/backups` | Backup directory |
| `RESIDENTS_BACKUP_ENABLED` | `true` | Disable backups with `false` |
| `RESIDENTS_BACKUP_REQUIRED` | `false` | Abort writes when an enabled backup fails |
| `RESIDENTS_BACKUP_RETENTION` | `10` | Number of timestamped backups to keep |
| `RESIDENTS_DB_INTEGRITY_CHECK` | `true` | Run `PRAGMA quick_check` on startup |
| `RESIDENTS_COOKIE_SECURE` | `true` | Require HTTPS-only session cookies; disable only for local HTTP development |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed browser origins |
| `RESIDENTS_MAX_REQUEST_BYTES` | `1000000` | Maximum request body size |
| `RESIDENTS_RATE_LIMIT_PER_MINUTE` | `300` | Per-client API limit; `0` disables |
| `RESIDENTS_TRUST_PROXY` | unset | Trust `X-Forwarded-For` for rate-limit keys |
| `RESIDENTS_HSTS` | unset | Enable HSTS behind HTTPS |
| `RESIDENTS_FRONTEND_DIR` | `<repo>/frontend/dist` | Built SPA directory |
| `VITE_API_BASE_URL` | `/api` | Frontend API base URL |

---

## Docker

The Dockerfile builds the React app in a Node stage, installs dependencies with
`npm ci` from the tracked lockfile, copies the result into a Python runtime
image, runs as a non-root user, stores data under `/data`, and includes a
healthcheck.

```bash
docker build -t residents-app .
docker run --rm -p 8000:8000 \
  -v residents-data:/data \
  -e RESIDENTS_COOKIE_SECURE=true \
  residents-app
```

Open [http://localhost:8000](http://localhost:8000). See
`docker-compose.example.yml` for a starting point.

**Verification:** the image built locally and an isolated, ephemeral container
smoke test confirmed `/health` returns `200`, an unauthenticated protected API
returns `401`, a protected direct page redirects to `/login`, `/login` returns
`200`, and registration is not available (`405`). The backend test suite covers
credential login and authenticated resident workflows. No real resident data
was used.

Docker remains a single-host SQLite deployment: do not run multiple replicas
against the same database file, and terminate TLS at a reverse proxy.

---

## API Reference

See [docs/api.md](docs/api.md) for the full endpoint reference.

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for a system overview.

---

## Security and privacy

**Implemented controls:**

- Operator-provisioned accounts, salted scrypt password hashes, HTTP-only server
  sessions, admin role checks, CSRF validation, logout/revocation, and enforced
  8-hour absolute / 30-minute idle session expiry.
- Protected API endpoints and server-side authorization for direct page loads;
  no public account registration.
- Pydantic validation, raw text storage with React output escaping, restrictive
  CSP, browser security headers, request limits, and bounded pagination.
- Configurable CORS (not authentication), privacy-safe error logs, SQLite
  integrity checks, and verified pre-write backups.

**Important limitations:**

- Access reads are not audited; only create/update/delete actions are recorded.
- Login throttling is in-process and per client, not distributed or a persistent
  account lockout.
- SQLite data and backups are not encrypted by the application; off-host backup,
  restore testing, and TLS configuration remain operational responsibilities.
- Hard delete is used, duplicate residents are allowed, and no general schema
  migration framework exists.
- Python dependencies are range-based; accessibility still needs manual WCAG
  and screen-reader review.

See [docs/gap-register.md](docs/gap-register.md) for the full findings and
remediation status.

---

## License

For demonstration and educational purposes only.
