# Residents Management System

A web application for managing resident records including personal details, qualifications, work experience, and skills.

The backend is a **FastAPI (Python)** JSON REST API backed by **SQLite** via **SQLAlchemy**.  
The frontend is a **React (Vite)** single-page application using **Bootstrap 5**.

---

## Features

- Create, view, edit, and delete residents
- Manage qualifications, work experience, and skills per resident
- Search by name, village, qualification field, or skill
- Server-side validation via Pydantic (including email format)
- Input sanitization against XSS on all API endpoints
- Inline toast notifications — no `alert()` / `confirm()` / `prompt()`
- Automatic timestamped database backups (last 10 kept)

---

## Project Structure

```
├── app/
│   ├── api_routes.py      # All JSON REST API endpoints
│   ├── main.py            # FastAPI app, CORS, lifespan
│   ├── models.py          # SQLAlchemy ORM models
│   ├── database.py        # DB engine, session, backup logic
│   ├── qualifications.py  # Qualification reference data
│   └── villages.py        # Village reference data
├── frontend/
│   ├── src/
│   │   ├── api/           # Axios API client
│   │   ├── components/    # Toast, EducationSection, ExperienceSection, SkillsSection
│   │   ├── hooks/         # useToast
│   │   ├── pages/         # Home, AddResident, EditResident, ViewResident, SearchResident
│   │   ├── App.jsx        # Router and global toast
│   │   └── main.jsx       # Entry point
│   ├── index.html
│   └── package.json
├── database/
│   ├── residents.db
│   └── backups/           # Auto-generated timestamped backups
├── docs/
│   ├── api.md             # Full API reference
│   ├── architecture.md    # System architecture overview
│   └── user-stories/      # Feature user stories
├── tests/
│   ├── test_form_submission.py  # Resident CRUD integration tests
│   ├── test_health.py           # API health and schema tests
│   ├── test_qualifications.py   # Qualifications endpoint tests
│   ├── test_validation.py       # Input validation tests
│   └── test_villages.py         # Villages endpoint tests
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Requirements

- Python **3.11+**
- Node.js **18+**

---

## Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload
```

- API: [http://localhost:8000](http://localhost:8000)
- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

The database and tables are created automatically on first startup.

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

React app: [http://localhost:5173](http://localhost:5173)

---

## Running Tests

```bash
# From the project root with the venv active
pytest tests/ -v
```

---

## Docker

```bash
docker build -t residents-app .
docker run -p 80:80 residents-app
```

---

## API Reference

See [docs/api.md](docs/api.md) for the full endpoint reference.

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for a system overview.

---

## Security

- All string inputs sanitized with `html.escape()` via Pydantic validators before persistence
- Email validated by Pydantic `EmailStr`
- CORS restricted to `http://localhost:5173` — update `app/main.py` for production
- No `alert()` / `confirm()` / `prompt()` in the frontend

---

## License

For demonstration and educational purposes only.
