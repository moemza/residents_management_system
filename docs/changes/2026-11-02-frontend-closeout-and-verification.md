# Change Record — Frontend Closeout and Deployment Verification

**Date:** 2026-11-02
**Branch:** `feature/react-frontend-migration`
**Baseline:** `32ab01e`
**Status:** Local working-tree changes; not committed or pushed. PR creation awaits
Project Owner approval.

This record covers the work completed after
[2026-10-31-full-remediation.md](2026-10-31-full-remediation.md). It closes the
remaining frontend accessibility/UX items and verifies the Docker image,
dependency audit, and full test suite.

---

## 1. Backend contracts and observability

**Files:** `app/schemas.py`, `app/api_routes.py`, `app/models.py`,
`app/rate_limit.py`, `app/main.py`, `app/database.py`, tests

**Behaviour:**

- Request and response models are explicit in `app/schemas.py`; OpenAPI now
  documents resident, qualification, experience, skill, audit, auth-status, and
  health shapes.
- Every create, update, and delete writes a non-PII `AuditEvent` in the same
  transaction. Update details record changed contact field **names** only.
- `GET /api/audit` supports `action`, `resident_id`, `limit`, and `offset` and
  returns `X-Total-Count`.
- `AuditEvent` has no foreign key to residents, so delete events survive record
  removal.
- Per-client sliding-window rate limiting applies to `/api/*` only. Excess
  requests return `429` with `Retry-After`; `/health` is exempt. The limiter
  bounds tracked keys and is documented as single-process.
- Every response carries `X-Request-ID`; well-formed caller IDs are reused.
  Supplied IDs are restricted to ASCII letters, digits, `.`, `_`, and `-` so a
  non-Latin-1 header value cannot break response serialisation.
- Bearer-token comparison encodes both values as UTF-8 before
  `secrets.compare_digest`, so a non-ASCII configured token returns a normal
  `401` rather than raising an error.
- API and health responses carry `Cache-Control: no-store`; additional
  cross-origin isolation headers were added.
- Startup runs `PRAGMA quick_check` before creating tables and indexes, and
  refuses to start on corruption.
- Backup retention is configurable; `RESIDENTS_BACKUP_REQUIRED=true` makes an
  enabled backup failure abort the write with `503`.

**New environment variables:** `RESIDENTS_BACKUP_REQUIRED`,
`RESIDENTS_BACKUP_RETENTION`, `RESIDENTS_DB_INTEGRITY_CHECK`,
`RESIDENTS_RATE_LIMIT_PER_MINUTE`, `RESIDENTS_TRUST_PROXY`.

---

## 2. Frontend closeout

**Files:** `frontend/src/App.jsx`, `pages/Residents.jsx`,
`pages/AddResident.jsx`, `pages/EditResident.jsx`, `pages/ViewResident.jsx`,
`pages/SearchResident.jsx`, `pages/Login.jsx`, `pages/Home.jsx`,
`components/ErrorBoundary.jsx`, `components/Toast.jsx`, dynamic sections,
`api/pagination.js`, `hooks/useDocumentTitle.js`, `api/residents.js`, tests

**Behaviour:**

- Added `/residents`, a paginated resident browser with total counts, empty
  state, error retry, and Previous/Next controls.
- Added shared pagination helpers and Node tests, including page clamping and
  invalid totals.
- Added a global render `ErrorBoundary` so a page crash does not leave a blank
  document.
- Added a skip link, `<main>` landmark, route focus transfer, and per-page
  browser titles.
- Add/Edit forms now mark required fields, expose validation errors through
  `aria-invalid`/`aria-describedby`, and focus the first invalid field.
- View page separates load errors from delete errors and restores focus to the
  Delete button when a confirmation is cancelled.
- Toast uses `role="alert"`/`role="status"` with an appropriate live region.
- Search distinguishes warnings from errors, uses readable API messages, keeps
  the active search for pagination, and links to the full resident browser.
- Login has an accessible description, required field, and invalid state.
- Section cards have headings and accessible add/remove controls.

**Limitation:** no full WCAG audit, manual keyboard walkthrough, or screen-reader
verification was performed.

---

## 3. Dependencies and CI

**Files:** `frontend/package-lock.json`, `.gitignore`,
`.github/workflows/ci.yml`, `Dockerfile`

- Confirmed `frontend/package-lock.json` is tracked; `.gitignore` now keeps it
  trackable while ignoring stray root-level lockfiles.
- Ran `npm audit fix`, which updated transitive/direct packages within the
  declared ranges and changed the audit result from 5 high-severity findings to
  **0 vulnerabilities**.
- Docker and CI now use `npm ci` instead of `npm install`, so a lockfile mismatch
  fails the build.
- Re-ran frontend tests, lint, build, and audit after the dependency update.

**Limitation:** Python dependencies remain range-based; no Python lockfile was
added.

---

## 4. Docker verification

**Files:** `Dockerfile`, `.dockerignore`, `docker-compose.example.yml`

The image was built and run with a temporary named volume, a synthetic token, and
synthetic resident data only. Verified:

| Check | Result |
|---|---|
| `docker build` | Passed |
| `/health` | `200 {"status":"ok","database":"ok"}` |
| Docker healthcheck | `healthy`, exit code `0` |
| Unauthenticated `/api/residents` | `401` |
| Authenticated `/api/residents` | `200`, empty list, `X-Total-Count: 0` |
| Create synthetic resident | `201` |
| Identity change on `PUT` | `409` |
| List and name search | `200`, one synthetic match |
| Audit | `200`, one `create` event |
| SPA `/` and `/residents` | `200`, built index returned |
| Headers | `X-Total-Count`, `X-Request-ID`, `Cache-Control: no-store`, CSP, COOP |
| Pre-write backup | One file under `/data/backups` |
| Runtime user | uid `999`, user `app` (non-root) |

The temporary container and volume were removed after the run. No production
system or real resident database was touched.

---

## 5. Verification summary

| Check | Result |
|---|---|
| Backend `pytest` | **179 passed** |
| Backend coverage | **92%** |
| `compileall` | Passed |
| `pip check` | No broken requirements |
| Frontend `npm test` | **9 passed** |
| Frontend lint | Passed, no warnings |
| Frontend build | Passed |
| `npm audit` | **0 vulnerabilities** |
| Docker build + smoke test | Passed |
| Configured database/backup metadata | Unchanged |

---

## 6. Remaining decisions and operational work

- Shared token only: no per-user identity, roles, expiry, revocation, or read
  access audit.
- No Python lockfile; Python dependency resolution remains range-based.
- Audit events have no retention, export, UI, or tamper-evidence policy.
- No distributed rate limiting, metrics, tracing, or alerting.
- Backups are local and unencrypted by default; off-host copies and a restore
  drill remain operational requirements.
- No general schema-migration framework; `create_all()` does not alter columns.
- Hard delete remains; duplicate-resident policy and soft-delete retention need
  product decisions.
- No full WCAG audit or assistive-technology verification.
- SQLite remains single-writer, one application instance per database file.

See [../gap-register.md](../gap-register.md) for the full register.
