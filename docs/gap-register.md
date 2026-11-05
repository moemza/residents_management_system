# Gap Register — Assessment and Remediation Record

**Assessment date:** 2026-10-31
**Last verification:** 2026-11-03
**Branch:** `feature/react-frontend-migration`
**Baseline commit:** `32ab01e`
**Status:** Implementation and independent security review complete on the
feature branch. Tests, frontend checks, Docker build, and isolated smoke test
passed. No production data was used; no deployment or access changes were made.

Severity: **P0** = critical, **P1** = high, **P2** = medium, **P3** = low.
Status: **Fixed**, **Partially fixed**, **Remaining**, **Decision required**, or
**Not verified**.

This register records verified findings from the read-only assessment and the
follow-up remediation. It distinguishes implemented controls from operational or
product decisions that remain open.

---

## P0 — Critical

| ID | Area | Finding | Resolution | Status |
|---|---|---|---|---|
| P0-1 | AuthN/AuthZ | No authentication or authorization existed; every endpoint was openly callable. | Implemented operator-provisioned admin accounts, scrypt password hashes, hashed opaque server sessions, admin role checks, CSRF checks, logout/revocation, 8-hour absolute and 30-minute idle expiry, server-side page guards, no public registration, and rejection of wildcard credentialed CORS. | **Fixed and independently reviewed** — read auditing, TLS and operational account provisioning remain requirements. |
| P0-2 | Test safety | Tests could create tables in, copy, and rotate backups of the configured application database. | `tests/conftest.py` now points `RESIDENTS_DB_PATH` and `RESIDENTS_BACKUP_DIR` at a temporary directory and disables backups before importing the app. Duplicated test clients were removed. | **Fixed** |
| P0-3 | Docker / privacy | No `.dockerignore`; `COPY . .` could place the database, backups, `.venv`, and `node_modules` into an image layer. No volume, non-root user, or frontend serving. | Added `.dockerignore`; multi-stage frontend build with tracked lockfile; non-root runtime user; `/data` volume; healthcheck; static SPA serving; runtime/dev requirements split. Built and smoke-tested locally on 2026-11-02. | **Fixed** |
| P0-4 | Destructive UX | Resident deletion had no real confirmation; `if (!window.confirm) return;` only checked that the API existed. | Replaced with an explicit confirmation panel naming the cascading consequences and requiring a second click. | **Fixed** |

---

## P1 — High

| ID | Area | Finding | Resolution | Status |
|---|---|---|---|---|
| P1-1 | Backup / recovery | Backups were post-commit `copy2` snapshots of a live SQLite file; no pre-write snapshot, integrity check, or restore test. Retention sorted by copied mtime. | Backups now use SQLite's online backup API before writes, verify with `PRAGMA quick_check`, use collision-safe timestamped names, retain the newest 10 by default (configurable), and support fail-closed writes. Added synthetic tests for readability, integrity, invalid sources, retention, and failure policy. | **Fixed in application** — off-host storage, encryption, freshness monitoring, and a restore drill remain operational requirements. |
| P1-2 | Data encoding / XSS | `html.escape()` was applied before persistence, causing double-escaped display/search values and putting output encoding in the wrong layer. | Removed escaping; values are trimmed, length-limited, and rejected if they contain `<`/`>`. React/JSX escapes output. Added a restrictive CSP and a dry-run-first migration utility for legacy escaped data. | **Fixed** |
| P1-3 | Search contract | UI sent a qualification field, but the API filtered qualification `name`; most field searches returned nothing. | Added field-to-name mapping in `api_routes.py` using `app/qualifications.py`; both field and name searches now work. Added regression tests. | **Fixed** |
| P1-4 | Privacy / performance | `GET /api/residents` returned every resident with no pagination or access control; list/search had N+1 child queries; search terms could appear in logs. | Added pagination with `X-Total-Count`, auth protection, eager loading with `selectinload`, search/village/FK indexes, request-size limits, privacy-safe error logging, per-client rate limiting, request IDs, and `no-store` API/health caching headers. | **Fixed in application** — distributed rate limiting and access-log configuration remain operational. |
| P1-5 | Validation / integrity | No maximum lengths or request-size limits; blank child rows accepted; identity fields mutable through the API. | Added documented length limits, child-row limits, blank-row rejection, markup rejection, request-size limit, and `409` identity immutability on `PUT`. Added tests. | **Fixed** — duplicate-resident policy remains a product decision. |
| P1-6 | Frontend error handling | FastAPI `422` returns `detail` as an array; rendering it directly in React could throw. | Added `frontend/src/api/errors.js` and used it in add/edit flows. Added Node tests for string, array, empty, and unknown details. | **Fixed** |

---

## P2 — Medium

| ID | Area | Finding | Resolution | Status |
|---|---|---|---|---|
| P2-1 | Configuration | API base URL and CORS origins were hard-coded. | Added `VITE_API_BASE_URL` (default `/api`), Vite dev/preview proxy, and `CORS_ORIGINS`. | **Fixed** |
| P2-2 | Database evolution | No migrations; `create_all()` does not alter existing tables; SQLite foreign keys were not explicitly enabled. | Enabled foreign keys, WAL, and busy timeout on every connection; added search/FK indexes and `CREATE INDEX IF NOT EXISTS` startup handling; added tests for FK enforcement and indexes. Added a targeted legacy-data migration utility. | **Partially fixed** — no general schema-migration framework; column changes still require a reviewed migration. |
| P2-3 | Documentation drift | README/architecture overstated test isolation and Docker completeness; test list and qualification examples were inaccurate. | Rewrote README, API, architecture, configuration, and operations documentation against the implementation. Added a dated change record. | **Fixed** |
| P2-4 | CI / frontend tests | No CI workflow and no frontend automated tests. | Added `.github/workflows/ci.yml` (backend tests/coverage, frontend tests/lint/build) and Node built-in tests for error and token helpers. | **Fixed** |
| P2-5 | Accessibility | Form labels were not associated with inputs; dynamic controls lacked accessible names. | Added `htmlFor`/`id`, `aria-label` on dynamic controls, `role="alertdialog"` and labelled text for delete confirmation, live regions for search messages/toasts, visible validation errors with `aria-invalid`/`aria-describedby`, a skip link, a `<main>` landmark, per-page titles, focus transfer on navigation, first-invalid-field focus, and delete-cancel focus restoration. Added a global error boundary. | **Partially fixed** — no full WCAG audit or screen-reader verification. |
| P2-6 | Dependencies | Python requirements were unpinned; `httpx2` was unused; no runtime/dev split. | Split `requirements.txt` (runtime) and `requirements-dev.txt`; added compatible version ranges; replaced unused `httpx2` with `httpx`, which `TestClient` requires; tracked `frontend/package-lock.json`; switched Docker/CI to `npm ci`; ran `npm audit fix`, reducing the reported vulnerabilities to **0**. | **Partially fixed** — no Python lockfile; Python resolution remains range-based. |
| P2-7 | Stale build artifacts | `frontend/dist/` is gitignored but present locally and may not match source. | Documented that the build must be regenerated; regenerated it for the Docker build and production smoke test. | **Fixed for the verified build** — rebuild remains part of deployment. |

---

## P3 — Low

| ID | Area | Finding | Resolution | Status |
|---|---|---|---|---|
| P3-1 | Docs | README test list omitted edge cases; architecture test description was inaccurate. | Corrected the test inventory and isolation description. | **Fixed** |
| P3-2 | Docker | README implied the frontend was served; the image only exposed the API. | Docker now builds and serves the SPA, uses a volume and non-root user, and documents TLS/proxy requirements. Build, runtime, healthcheck, auth, CRUD, backups, and SPA fallback were verified on 2026-11-02. | **Fixed** |
| P3-3 | UX | Edit page showed a toast on load failure but left an empty form. | Added an explicit load-error state with a Home link; add page now surfaces reference-data load failures. | **Fixed** |
| P3-4 | Security headers | No CSP/HSTS/security headers or HTTPS guidance. | Added CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, cross-origin isolation headers, `Cache-Control: no-store` for API/health, and opt-in HSTS; documented TLS termination. | **Fixed** |
| P3-5 | Soft delete / audit | Hard delete removes records with no audit trail. | Added delete confirmation, a pre-write backup, and a non-PII delete audit event that survives resident removal. | **Partially fixed** — hard delete/retention and audit export policy remain product decisions. |

---

## Newly recorded remaining risks

| ID | Area | Risk | Status |
|---|---|---|---|
| R-1 | AuthN/AuthZ | Read access is not audited; sessions use the configured SQLite database and in-process login throttling. | Admin identity, role enforcement, session expiry, and logout are implemented; review pending. | **Partially fixed / operational** — read audit and distributed rate limiting remain. |
| R-2 | Rate limiting | In-process per-client limiting is implemented (default 300/minute, `429` + `Retry-After`). It resets on restart, is not shared across processes, and is not an account lockout or brute-force control. | **Partially fixed / operational** — use a proxy/platform limit for multi-instance deployments. |
| R-3 | Backups | Backups are local, unencrypted, and not monitored for freshness; no automated off-host copy or restore drill. | **Remaining operational** |
| R-4 | Encryption | SQLite data and backups are not encrypted by the application; rely on disk/volume encryption and access controls. | **Remaining operational** |
| R-5 | Duplicate residents | No uniqueness rule; identical residents can be created. | **Decision required** — product rule needed. |
| R-6 | Schema migrations | No general migration framework; `create_all()` does not alter existing columns. | **Remaining** |
| R-7 | Scaling | SQLite is single-writer; one application instance per database file. No HA or read replicas. | **Documented limitation** |
| R-8 | Accessibility | Accessibility improved with landmarks, skip link, page titles, error boundary, focus management, and labelled errors, but there is no full WCAG audit, manual keyboard walkthrough, or screen-reader verification. | **Partially fixed** |
| R-9 | Docker | Image build, non-root runtime, healthcheck, static serving, auth, CRUD, and backups were executed with a temporary volume and synthetic data. Production TLS/storage still require an approved environment. | **Verified locally** |
| R-10 | Dependency locking | Frontend lockfile is tracked and Docker/CI use `npm ci`; `npm audit` reported 0 vulnerabilities after fixes. Python dependencies still resolve from ranges and have no lockfile. | **Partially fixed** |
| R-11 | Audit logging | Non-PII create/update/delete events are recorded with request IDs and a `shared-token`/`anonymous` actor class. Reads, a UI, retention, export, tamper-evidence, and a formal access policy are absent. | **Partially fixed / decision required** |
| R-12 | Error observability | Request IDs are returned and recorded in audit events, but there are no metrics, tracing, structured log aggregation, or alerting. | **Partially fixed** |
| R-13 | Request-size enforcement | The in-app limit checks `Content-Length`; chunked requests without it are not rejected there. A reverse-proxy body limit is recommended. | **Documented limitation** |
| R-14 | Audit retention | Audit rows are retained indefinitely with no archival or deletion policy, and they share the SQLite database. | **Decision required** |

---

## Changes applied

### Safety and isolation

- `tests/conftest.py`: temporary database, temporary backup directory, backups
  disabled, rate limiting disabled, and startup integrity checking disabled
  before app import.
- `tests/test_configuration.py`: asserts isolation and CORS parsing.
- `tests/test_database_backup.py`, `tests/test_database_integrity.py`: backup
  safety, configurable retention, startup integrity, FK pragma, indexes, orphan
  rejection.
- `tests/test_backup_behavior.py`: best-effort versus fail-closed backup failure.

### Backend

- `app/auth.py`: operator-provisioned password verification, server-side admin sessions, CSRF, and role enforcement.
- `app/schemas.py`: explicit request/response contracts and validation limits.
- `app/rate_limit.py`: bounded in-process sliding-window limiter.
- `app/api_routes.py`: auth, validation limits, markup rejection, identity
  immutability, pagination, qualification field mapping, literal LIKE escaping,
  eager loading, pre-write backups, and non-PII audit events.
- `app/database.py`: configurable paths, SQLite online backup with integrity
  check, configurable retention, optional fail-closed writes, startup integrity
  verification, FK/WAL/busy-timeout pragmas, index creation.
- `app/main.py`: CORS, request-size limit, rate limiting, request IDs, security
  and cache headers, startup integrity check, health endpoint, auth status,
  privacy-safe error logging, SPA serving.
- `app/migrations.py`, `scripts/migrate_unescape.py`: safe legacy-data
  normalisation.
- `app/models.py`: indexes on search/FK columns and `AuditEvent`.
- `requirements.txt`, `requirements-dev.txt`: runtime/dev split and version
  ranges.

### Frontend

- `frontend/src/auth.js`, `pages/Login.jsx`, `App.jsx`: auth status, login,
  session token, guard, 401 handling, skip link, main landmark, route focus
  transfer, and error boundary.
- `frontend/src/api/residents.js`: same-origin `/api` default, token interceptor,
  401 handling, and paginated list/search helpers.
- `frontend/src/api/pagination.js`: tested page-range and clamping helpers.
- `frontend/src/pages/Residents.jsx`: paginated resident browser.
- `frontend/src/pages/SearchResident.jsx`: server pagination, readable API
  errors, and browse-all link.
- `frontend/src/pages/AddResident.jsx`, `EditResident.jsx`: error normalization,
  load-error states, required/ARIA validation, first-invalid-field focus.
- `frontend/src/pages/ViewResident.jsx`: explicit delete confirmation, separate
  action errors, and focus restoration.
- `frontend/src/components/*`: section headings, accessible dynamic controls,
  live-region toast, and global error boundary.
- `frontend/src/hooks/*`: toast state and per-page document titles.
- `frontend/tests/*`: Node tests for error, token, and pagination helpers.
- `frontend/vite.config.js`: `/api` dev/preview proxy.

### Deployment and CI

- `Dockerfile`: multi-stage frontend build with `npm ci`, non-root user, `/data`
  volume, healthcheck, port 8000.
- `.dockerignore`: excludes data, backups, dependencies, build output, docs,
  tests, and local env files.
- `docker-compose.example.yml`: example volume/token configuration.
- `.github/workflows/ci.yml`: backend tests/coverage, frontend tests/lint/build
  using `npm ci`.
- `.gitignore`: keeps the frontend lockfile trackable while ignoring stray root
  lockfiles.
- `frontend/package-lock.json`: refreshed through `npm audit fix`; `npm audit`
  now reports 0 vulnerabilities.

### Documentation

- Rewrote `README.md`, `docs/api.md`, `docs/architecture.md`,
  `docs/configuration.md`, and `docs/operations.md`.
- Added `docs/gap-register.md` and dated change records under `docs/changes/`.
- Updated `docs/user-stories/search_resident_page.md`.

---

## Verification record

Local results on 2026-11-02:

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | **179 passed** |
| `.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing -q` | **179 passed**, **92% total coverage** |
| `python -m compileall app scripts tests` | **Passed** |
| `python -m pip check` | **No broken requirements** |
| `npm test` (frontend) | **9 passed** |
| `npm run lint` (frontend) | **Passed**, no warnings |
| `npm run build` (frontend) | **Passed** |
| `npm audit` (frontend) | **0 vulnerabilities** after `npm audit fix` |
| `docker build` | **Passed** |
| Docker run smoke test | **Passed** — `/health` 200; healthcheck `healthy`; 401 without token; authenticated create/list/search/audit; 409 identity change; SPA `/` and `/residents`; `X-Total-Count`, `X-Request-ID`, `no-store`, CSP; pre-write backup; non-root uid 999 (`app`) |
| Configured DB/backup metadata before vs. after tests | **Unchanged** (size/mtime and backup filenames/sizes) |
| Real resident database access | **None** — only file metadata compared |

The configured `database/residents.db` and its existing backups were not opened,
queried, copied, or disclosed. Tests and the Docker smoke test use synthetic data
only. Docker used a temporary named volume that was removed after the run.

The remaining items in the tables above are product or operational decisions,
not unverified claims. In particular, no real resident database migration has
been executed, and no production deployment has been changed.

---

## 2026-11-03 administrator authentication and UI completion

**Branch:** `feature/react-frontend-migration`
**Candidate commit:** pending
**Status:** implementation and independent security review complete; publication
is pending the project owner's authorized commit/push/PR workflow.

**Implemented:** operator-provisioned admin accounts, scrypt password hashes,
hashed server-side sessions, admin-only API and direct-page checks, CSRF
validation, logout and account revocation, 8-hour absolute/30-minute idle
expiry, responsive app navigation, updated dashboard/login, loading and
authentication error states, and accessibility focus/label improvements.
Public health and auth-status endpoints remain available without resident data.
Credentialed CORS rejects wildcard origins.

**Verified checks:**

- `.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing -q` —
  **182 passed**, **92% total application coverage**.
- `cd frontend && npm test` — **9 passed**.
- `cd frontend && npm run lint` — passed.
- `cd frontend && npm run build` — passed.
- `cd frontend && npm audit --omit=dev` — **0 vulnerabilities**.
- `.venv/bin/python -m compileall -q app scripts tests` — passed.
- `.venv/bin/python -m scripts.provision_admin --help` — passed.
- `git diff --check` — passed.
- `docker build --tag residents-management-system:auth-review .` — passed.
- Isolated Docker smoke test — health `200`, unauthenticated API `401`,
  protected direct URL `303` to login, login page `200`, registration `405`;
  temporary container stopped and removed.
- Independent security review — identified and then verified the wildcard
  credentialed-CORS rejection. No remaining high/critical issue was identified.

**Not performed:** manual screen-reader/WCAG audit, deployment validation,
production access changes, migration of a real database, or tests against real
resident data. Read auditing and distributed login throttling remain
limitations; deploy with HTTPS and explicit trusted CORS origins.
