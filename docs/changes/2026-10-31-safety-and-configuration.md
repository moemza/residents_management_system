# Change Record — Safety, Configuration, and Error-Handling Fixes

**Date:** 2026-10-31
**Branch:** `feature/react-frontend-migration`
**Baseline:** `32ab01e`
**Status:** Local working-tree changes; not committed or pushed.

> **Superseded:** this record documents the first low-risk batch. The full
> remediation is recorded in
> [2026-10-31-full-remediation.md](2026-10-31-full-remediation.md). Some
> limitations below were addressed in the later batch.

---

## Purpose

Address low-risk findings from the project assessment without changing core
resident data semantics or introducing an authentication architecture without
owner approval. The batch focuses on test safety, deployment hygiene,
destructive-action safety, configuration, and readable API errors.

---

## Changes

### 1. Test isolation and backup disablement

**Files:** `tests/conftest.py`, `tests/test_form_submission.py`,
`tests/test_validation.py`, `tests/test_configuration.py`

**Behaviour:**

- Tests create a temporary directory and set `RESIDENTS_DB_PATH`,
  `RESIDENTS_BACKUP_DIR`, and `RESIDENTS_BACKUP_ENABLED=false` before importing
  the application.
- The temporary directory is removed at process exit.
- `test_form_submission.py` and `test_validation.py` now use the shared
  `client` fixture instead of defining separate module-level engines and
  clients.
- A configuration test asserts that the test DB is not the configured
  application DB and that backups are disabled.

**Why:** The previous suite could create tables in, copy, and rotate backups of
the configured application database. This was a privacy and data-safety risk.

**Limitation:** Tests still use a file-based SQLite database in a temporary
directory, not an in-memory database. This is intentional so the application
lifespan and SQLAlchemy configuration are exercised realistically.

### 2. Configurable runtime paths and CORS

**Files:** `app/database.py`, `app/main.py`, `docs/configuration.md`,
`README.md`

**Behaviour:**

| Variable | Default |
|---|---|
| `RESIDENTS_DB_PATH` | `<repo>/database/residents.db` |
| `RESIDENTS_BACKUP_DIR` | `<repo>/database/backups` |
| `RESIDENTS_BACKUP_ENABLED` | `true` |
| `CORS_ORIGINS` | `http://localhost:5173` |

Defaults preserve existing local behaviour. `create_tables()` now creates the
database parent directory if needed.

**API changes:** None. Endpoint paths, request bodies, and response shapes are
unchanged.

### 3. Backup filename and retention safety

**Files:** `app/database.py`, `tests/test_database_backup.py`

**Behaviour:**

- Backup filenames include microseconds and a collision suffix so two writes in
  the same second cannot overwrite an existing backup.
- Retention sorts by the timestamped filename rather than copied file mtime.
- Backups can be disabled through `RESIDENTS_BACKUP_ENABLED`.
- New tests verify disabled-backup behavior and the 10-file retention limit
  using synthetic data in a temporary directory.

**Limitations:** Backups are still post-write `shutil.copy2` copies, not
consistent SQLite snapshots. There is no pre-write recovery point, integrity
check, restore drill, off-host copy, or encryption. A full backup redesign
requires owner approval.

### 4. Docker build-context hygiene

**Files:** `.dockerignore`

**Behaviour:** Excludes `.git`, `.venv`, caches, `database/`, SQLite files,
backups, `frontend/node_modules`, `frontend/dist`, and local environment files
from the Docker build context.

**Limitation:** The Dockerfile still builds only the FastAPI API; it does not
serve the React frontend, persist SQLite data on a volume, or run as a non-root
user. Docker is not a verified production path.

### 5. Delete confirmation

**Files:** `frontend/src/pages/ViewResident.jsx`

**Behaviour:** The Delete button now opens an inline confirmation panel that
names the cascading consequences and requires a second explicit click. Cancel
returns to the normal footer. The ineffective `window.confirm` guard was
removed.

**API changes:** None. `DELETE /api/residents/{id}` remains a hard delete.

**Limitation:** This is a confirmation guard, not an undo or audit trail. A
soft-delete/audit policy remains a product decision.

### 6. Frontend API error normalisation

**Files:** `frontend/src/api/errors.js`,
`frontend/src/pages/AddResident.jsx`, `frontend/src/pages/EditResident.jsx`

**Behaviour:** FastAPI `detail` values are converted to a readable string.
String details are passed through; arrays of validation objects are formatted as
`field: message` entries joined with semicolons; unknown shapes fall back to a
page-specific message.

**Why:** FastAPI 422 responses return an array. Rendering that array directly in
React can throw “Objects are not valid as a React child”.

**Limitation:** There is no frontend test runner in the repository yet; this
path is covered by lint/build checks and manual verification, not automated
frontend tests.

### 7. Privacy-safe error logging

**Files:** `app/main.py`

**Behaviour:** The global exception handler logs `request.url.path` and the
exception type instead of the full URL and exception string. Query strings are
no longer included in this log message.

**Limitation:** Uvicorn access logs and other process logging still need
operational configuration to avoid recording search terms or personal data.

### 8. Frontend configuration and accessibility

**Files:** `frontend/src/api/residents.js`, `frontend/.env.example`,
`frontend/src/pages/AddResident.jsx`, `frontend/src/pages/EditResident.jsx`,
`frontend/src/pages/SearchResident.jsx`, frontend section components

**Behaviour:**

- API base URL uses `VITE_API_BASE_URL` with the existing localhost fallback.
- Form labels are associated with inputs via `htmlFor`/`id`.
- Dynamic child-row controls have accessible labels.
- Delete confirmation uses `role="alertdialog"` and labelled text.

**API changes:** None.

**Limitation:** This is not a full WCAG audit. Keyboard/focus behavior and
screen-reader verification still need manual testing.

---

## Tests added or updated

- `tests/test_configuration.py` — verifies test DB isolation, backup
  disablement, and CORS-origin parsing.
- `tests/test_database_backup.py` — verifies disabled backups and 10-file
  retention using synthetic SQLite data.
- `tests/test_form_submission.py` — now uses the shared isolated `client`
  fixture.
- `tests/test_validation.py` — now uses the shared isolated `client` fixture.

Existing tests remain unchanged in intent and use synthetic data.

---

## Verification instructions

```bash
# From the repository root, with the backend virtual environment active
pytest tests/ -v

# Coverage
pytest tests/ --cov=app --cov-report=term-missing

# Frontend checks
cd frontend
npm run lint
npm run build
```

Before running tests, confirm the test environment variables are set by
`tests/conftest.py`; do not run against a database containing real resident
data.

---

## Verification evidence (local, 2026-10-31)

| Check | Result |
|---|---|
| `.venv/bin/python -m pytest tests/ -q` | **100 passed** |
| `.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing -q` | **100 passed**, 92% total coverage |
| `npm run lint` | **Passed** (no warnings) |
| `npm run build` | **Passed** (Vite production build) |
| API error helper manual Node check | **Passed** (string, 422 array, fallback) |
| Configured DB/backup metadata before vs. after tests | **Unchanged** (size/mtime and backup filenames/sizes) |
| Docker build | **Not run** — avoids package installation and is outside this low-risk batch |

The configured `database/residents.db` and its 10 existing backups were not
opened or queried. Only file metadata was compared before and after the test
runs.

---

## Known limitations and follow-up

- No authentication or authorization.
- Qualification field search contract remains broken except for `"Law"`.
- `html.escape` persistence and search semantics remain unchanged.
- No pagination on resident listings.
- Backup recovery is not verified; backup redesign needs approval.
- No migrations or database-level foreign-key enforcement.
- No CI or frontend automated tests.
- Docker does not serve the frontend or provide durable storage.
- Validation limits, duplicate policy, and identity-field immutability still
  require product decisions.

See [gap-register.md](gap-register.md) for the prioritised register.
