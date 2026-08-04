# Architecture

## Overview

The system follows a standard client-server architecture with a clear separation between the React frontend and the FastAPI backend.

```
┌─────────────────────────────┐        HTTP/JSON        ┌──────────────────────────────┐
│        React SPA            │ ──────────────────────► │      FastAPI Backend         │
│     (Vite, port 5173)       │ ◄────────────────────── │      (uvicorn, port 8000)    │
└─────────────────────────────┘                         └──────────────┬───────────────┘
                                                                        │ SQLAlchemy ORM
                                                                        ▼
                                                         ┌──────────────────────────────┐
                                                         │        SQLite Database       │
                                                         │    database/residents.db     │
                                                         └──────────────────────────────┘
```

---

## Backend (`app/`)

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app instance, CORS middleware, lifespan (DB init), router registration |
| `api_routes.py` | All REST endpoints — residents CRUD, search, villages, qualifications |
| `models.py` | SQLAlchemy ORM models: `Resident`, `Qualification`, `Experience`, `Skill` |
| `database.py` | Engine setup, session factory, `get_db` dependency, `backup_database()` |
| `qualifications.py` | Static reference data: types, fields, levels, names |
| `villages.py` | Static village list |

### Request lifecycle

1. React sends an HTTP request via Axios to `/api/...`
2. FastAPI routes the request to the matching handler in `api_routes.py`
3. Pydantic validates and sanitizes the request body (`html.escape` on all string fields)
4. The handler uses a SQLAlchemy `Session` (injected via `Depends(get_db)`) to query or mutate the DB
5. On write operations, `backup_database()` creates a timestamped copy in `database/backups/`
6. The handler returns a plain `dict` serialized to JSON

### Database

- SQLite file at `database/residents.db`
- Tables are created automatically on startup via `Base.metadata.create_all()`
- Backups are stored in `database/backups/` — the last 10 are kept, older ones are deleted automatically

### Data model

```
Resident
  ├── id, first_name, last_name, dob, gender, village
  ├── cellphone_no, cellphone_no2, email
  ├── qualifications  →  Qualification (institution, name, type, level, year)
  ├── experiences     →  Experience (company, position, years)
  └── skills          →  Skill (name)
```

All child records use `cascade="all, delete-orphan"` so deleting a resident removes all related records.

---

## Frontend (`frontend/src/`)

| Path | Responsibility |
|------|---------------|
| `api/residents.js` | Centralized Axios client — all API calls in one place |
| `pages/Home.jsx` | Landing page with navigation links |
| `pages/AddResident.jsx` | Form to create a new resident with client-side validation |
| `pages/EditResident.jsx` | Pre-populated form to update an existing resident |
| `pages/ViewResident.jsx` | Read-only view of a resident's full details |
| `pages/SearchResident.jsx` | Search form with dynamic input based on search type |
| `components/EducationSection.jsx` | Dynamic add/remove education rows |
| `components/ExperienceSection.jsx` | Dynamic add/remove experience rows |
| `components/SkillsSection.jsx` | Dynamic add/remove skill rows |
| `components/Toast.jsx` | Auto-dismissing notification banner |
| `hooks/useToast.js` | State management for toast notifications |
| `App.jsx` | Route definitions, global toast for post-navigation messages |
| `main.jsx` | React root, BrowserRouter, Bootstrap CSS import |

### Data flow (create resident example)

1. User fills the form in `AddResident.jsx`
2. On submit, client-side validation runs — errors shown inline via Bootstrap `is-invalid`
3. If valid, `createResident(payload)` in `api/residents.js` sends `POST /api/residents`
4. On success, `navigate("/", { state: { success: "..." } })` redirects to Home
5. `App.jsx` reads `location.state.success` and shows a `Toast`
6. On error, the caught Axios error message is shown in a `Toast` inline

### Routing

| Path | Component |
|------|-----------|
| `/` | `Home` |
| `/add-resident` | `AddResident` |
| `/edit-resident/:id` | `EditResident` |
| `/view-resident/:id` | `ViewResident` |
| `/search` | `SearchResident` |

---

## Security

- **XSS prevention** — all string inputs are sanitized with `html.escape()` in Pydantic `@field_validator` before any data reaches the database
- **Email validation** — Pydantic `EmailStr` rejects malformed email addresses at the API layer
- **Future DOB rejection** — `dob` is validated to not exceed today's date; returns `422` if it does
- **CORS** — restricted to `http://localhost:5173`; update `allow_origins` in `app/main.py` before deploying
- **No raw HTML injection** — the React frontend uses JSX which escapes all values by default; no `dangerouslySetInnerHTML` is used anywhere
- **No browser dialogs** — all user feedback uses the `Toast` component

## Tests (`tests/`)

| File | Covers |
|------|--------|
| `conftest.py` | Shared in-memory DB fixture and base resident payload |
| `test_health.py` | `/docs` availability, OpenAPI schema title |
| `test_villages.py` | `GET /api/villages` shape and content |
| `test_qualifications.py` | `GET /api/qualifications` shape and content |
| `test_validation.py` | Required fields, email format, date format, empty search |
| `test_form_submission.py` | Full resident CRUD via the API |
| `test_integration_add_resident.py` | Add Resident user stories US-01 – US-07 |
| `test_integration_edit_resident.py` | Edit Resident user stories US-ER-01 – US-ER-06 |
| `test_integration_search_resident.py` | Search Resident user stories US-SR-01 – US-SR-08 |

All tests use an isolated SQLite test database (`database/test_residents.db`) that is created and torn down per test via the `client` fixture in `conftest.py`.

### Commands

```bash
# Run the full suite
pytest tests/ -v

# Run only integration tests (user-story coverage)
pytest tests/ -v -k "integration"

# Run a single file
pytest tests/test_integration_add_resident.py -v
pytest tests/test_integration_edit_resident.py -v
pytest tests/test_integration_search_resident.py -v

# Run with coverage (terminal report)
pytest tests/ --cov=app --cov-report=term-missing

# Run with coverage (HTML report — open htmlcov/index.html)
pytest tests/ --cov=app --cov-report=html

# Short pass/fail summary
pytest tests/ -q
```

---


- Villages: edit the `VILLAGES` list in `app/villages.py`
- Qualification types/levels/fields/names: edit the corresponding constants in `app/qualifications.py`

No database migration is needed — these are static reference lists served directly from the API.
