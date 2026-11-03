# Change Record — Full Remediation

**Date:** 2026-10-31
**Branch:** `feature/react-frontend-migration`
**Baseline:** `32ab01e`
**Status:** Local working-tree changes; not committed or pushed. PR creation awaits
Project Owner approval.

This record supersedes and extends
[2026-10-31-safety-and-configuration.md](2026-10-31-safety-and-configuration.md).

> **Follow-up (2026-11-02):** later work added response contracts, write audit
> events, request IDs, rate limiting, startup integrity checks, configurable
> backup retention/fail-closed behaviour, the residents list UI, error boundary,
> skip link/focus work, dependency audit fixes, and full Docker build/runtime
> verification. See
> [2026-11-02-frontend-closeout-and-verification.md](2026-11-02-frontend-closeout-and-verification.md)
> and the current verification record in
> [../gap-register.md](../gap-register.md). Where this record says a control is
> absent or unverified, the 2026-11-02 record is authoritative.

---

## Purpose

Close the prioritised gaps found in the application assessment across backend,
frontend, API contracts, authentication, validation, error handling, security,
performance, accessibility, testing, configuration, and deployment readiness.
All testing used synthetic data. No real resident database contents were opened,
queried, copied, or disclosed.

---

## 1. Authentication and access control

**Files:** `app/auth.py`, `app/main.py`, `app/api_routes.py`,
`frontend/src/auth.js`, `frontend/src/pages/Login.jsx`, `frontend/src/App.jsx`,
`frontend/src/api/residents.js`

**Behaviour:**

- `RESIDENTS_API_TOKEN` enables a shared bearer-token requirement for `/api/*`.
- Missing or invalid tokens return `401` with `WWW-Authenticate: Bearer`.
- `GET /api/auth/status` is public and reports whether auth is required.
- `GET /api/auth/verify` requires a valid token.
- `GET /health` remains public for probes.
- The React app checks auth status, redirects to `/login`, stores the token in
  `sessionStorage`, adds the bearer header, and clears the token on `401`.

**Trade-off:** a shared token is the minimum deployable control for a
single-tenant system. It does not provide per-user identity, roles, audit,
expiry, or revocation. Those require a product/security decision.

**API changes:** new auth endpoints; `401` responses when configured. Existing
unauthenticated local development remains unchanged when the variable is unset.

---

## 2. Validation, data integrity, and API contract

**Files:** `app/api_routes.py`, `app/models.py`, tests

**Behaviour:**

- Required text fields are trimmed and rejected when blank.
- Length limits: names/gender/village 100; phone 30; email 254; most child text
  200; year/years 20; skill name 100.
- At most 50 qualifications, experiences, and skills per resident.
- `<` and `>` are rejected as HTML markup.
- Optional blank strings become `null`.
- Future dates of birth return `422`.
- `PUT` rejects changes to `first_name`, `last_name`, `dob`, `gender`, or
  `village` with `409`.
- List and search endpoints support `limit` (1–500, default 100) and `offset`
  (`>= 0`) and return `X-Total-Count`.
- Search query length is capped at 200; unknown `search_type` returns `422`.
- Qualification search maps a field such as `Information Technology` to its
  known qualification names, while still accepting a name directly.
- `%` and `_` in search terms are treated literally.
- Duplicate residents remain allowed; uniqueness is a product decision.

**API changes:** `409` for identity changes, `422` for previously accepted
oversized/markup/unknown-search-type inputs, `X-Total-Count` headers, new
pagination parameters.

---

## 3. Data encoding and legacy migration

**Files:** `app/api_routes.py`, `app/migrations.py`,
`scripts/migrate_unescape.py`, `tests/test_migrations.py`

**Behaviour:**

- Removed `html.escape` before persistence.
- Raw text is stored and escaped by React at render time.
- Markup is rejected at the API boundary.
- The migration utility reports legacy escaped values by default (dry run) and
  can apply changes with `--apply`.
- Applying creates and integrity-checks a pre-migration backup, uses a fixed
  column allow-list, updates in one transaction, and is idempotent.
- The CLI requires an explicit `--db` path and never selects the repository
  database implicitly.

**Compatibility:** existing escaped data is not modified automatically. It can
be normalised with the utility after review. Values that become markup after
unescaping are stored as raw text and safely rendered by React; new markup is
rejected.

---

## 4. Backups and database reliability

**Files:** `app/database.py`, `tests/test_database_backup.py`,
`tests/test_database_integrity.py`

**Behaviour:**

- Backups use SQLite's online backup API for a consistent snapshot.
- A pre-write backup is taken before create, update, and delete when enabled.
- Each backup is verified with `PRAGMA quick_check`; failed files are removed.
- Filenames include microseconds and a collision suffix.
- The newest 10 backups are retained by timestamped filename.
- Every SQLite connection enables foreign keys, a 5-second busy timeout, and WAL.
- Missing search and foreign-key indexes are created on startup.
- List/search queries eager-load child rows to avoid N+1 queries.

**Limitations:** backups remain local, unencrypted, and unmonitored; off-host
copies and restore drills are operational requirements.

---

## 5. HTTP security and operations

**Files:** `app/main.py`, tests

**Behaviour:**

- Request bodies above `RESIDENTS_MAX_REQUEST_BYTES` (default 1,000,000) return
  `413`.
- Security headers: CSP, `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`, and opt-in HSTS.
- `GET /health` checks the database with `SELECT 1` and returns `503` when
  unavailable.
- Error logs omit query strings and exception messages; stack frames are kept.
- The built SPA is served from `RESIDENTS_FRONTEND_DIR` with a safe client-side
  routing fallback. `/api/*` and `/health` are never masked by the SPA.
- CORS remains configurable through `CORS_ORIGINS`.

**Limitations:** no rate limiting, audit log, metrics, tracing, or TLS
termination inside the application.

---

## 6. Frontend UX, errors, and accessibility

**Files:** frontend pages, components, `api/errors.js`, `api/residents.js`,
`auth.js`, `App.jsx`, `vite.config.js`

**Behaviour:**

- FastAPI error details are normalised to readable strings.
- Add/Edit pages show load failures instead of an empty form.
- Delete uses an explicit confirmation panel with `role="alertdialog"` and
  labelled consequences.
- Form labels are associated with inputs; dynamic row controls have accessible
  names; search messages and result counts use live regions.
- Search results are paginated with Previous/Next and a visible total.
- API base URL defaults to `/api`; Vite proxies it to the backend in development.
- The auth guard redirects to login when required and clears invalid tokens.

**Limitations:** no full WCAG audit or screen-reader verification.

---

## 7. Tests, CI, and dependencies

**Files:** `tests/*`, `frontend/tests/*`, `.github/workflows/ci.yml`,
`requirements.txt`, `requirements-dev.txt`, `frontend/package.json`

**Behaviour:**

- Backend tests remain isolated on a temporary database with backups disabled.
- Added tests for auth, pagination, qualification-field search, LIKE escaping,
  identity immutability, validation limits, health, headers, request size,
  indexes, foreign keys, backup integrity, and migrations.
- Added frontend Node tests for error normalisation and token helpers.
- Added a CI workflow for backend tests/coverage and frontend tests/lint/build.
- Split runtime and development requirements; replaced unused `httpx2` with
  `httpx`, which `TestClient` requires; added compatible version ranges.

**Limitations:** no Python lockfile. The frontend lockfile was untracked at the
time of this record; it is now tracked and both Docker and CI use `npm ci` (see
the 2026-11-02 record).

---

## 8. Deployment and documentation

**Files:** `Dockerfile`, `.dockerignore`, `docker-compose.example.yml`,
`README.md`, `docs/*`

**Behaviour:**

- Multi-stage Docker build compiles the frontend and copies it into a Python
  runtime image.
- Runs as a non-root user, stores data under `/data`, exposes port 8000, and
  includes a `/health` healthcheck.
- `.dockerignore` excludes resident data, backups, dependencies, build output,
  docs, tests, and local env files.
- Documentation rewritten for actual behaviour, configuration, API contracts,
  operations, recovery, migrations, and remaining risks.

**Limitation:** the Docker image was not built or run in this environment
because package installation was not authorised.

---

## Verification

See the final completion report for exact commands and results. At the time of
this record, the backend suite passed with 147 tests, frontend tests passed (5),
lint passed with no warnings, and the production build passed. These counts were
superseded by the 2026-11-02 record (179 backend tests, 9 frontend tests, 92%
coverage, Docker verified).

---

## Known limitations and follow-up

- Shared token only; no per-user roles, audit, expiry, or revocation.
- No rate limiting, account lockout, or application-level audit trail.
- Backups are local and unencrypted; no automated off-host copy or restore drill.
- No general schema-migration framework.
- Duplicate-resident policy and soft-delete/audit policy need product decisions.
- SQLite is single-writer; one instance per database file.
- Docker build and runtime are unverified.
- No full accessibility audit.
- No Python lockfile.

See [../gap-register.md](../gap-register.md) for the full register.
