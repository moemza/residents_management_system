# Configuration

Runtime paths, authentication, CORS, request limits, backups, and the frontend
API URL are configurable through environment variables. Defaults preserve the
local development setup.

Environment variables are read from the process environment. The backend does
not load a `.env` file automatically, so export variables in your shell or use
your process manager's environment configuration. Never commit real tokens or
resident data.

---

## Backend

| Variable | Default | Purpose |
|---|---|---|
| `RESIDENTS_DB_PATH` | `<repo>/database/residents.db` | SQLite database file |
| `RESIDENTS_BACKUP_DIR` | `<repo>/database/backups` | Timestamped backup directory |
| `RESIDENTS_BACKUP_ENABLED` | `true` | Set to `false`, `0`, `no`, or `off` to disable backups |
| `RESIDENTS_BACKUP_REQUIRED` | `false` | Abort a write with `503` when an enabled backup fails |
| `RESIDENTS_BACKUP_RETENTION` | `10` | Number of newest backups to retain (minimum 1) |
| `RESIDENTS_DB_INTEGRITY_CHECK` | `true` | Run `PRAGMA quick_check` before startup table creation |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated browser origins |
| `RESIDENTS_COOKIE_SECURE` | `true` | Require HTTPS-only session cookies; disable only for local HTTP development |
| `RESIDENTS_MAX_REQUEST_BYTES` | `1000000` | Maximum request body size in bytes |
| `RESIDENTS_RATE_LIMIT_PER_MINUTE` | `300` | Per-client `/api/*` limit; `0` disables limiting |
| `RESIDENTS_TRUST_PROXY` | unset | Trust `X-Forwarded-For` for rate-limit keys |
| `RESIDENTS_HSTS` | unset | Set to `true` to emit HSTS when served over HTTPS |
| `RESIDENTS_FRONTEND_DIR` | `<repo>/frontend/dist` | Built SPA directory served by FastAPI |

Provision an admin account using the same configured database path as the
application. The CLI prompts for the password and stores only its salted scrypt
hash:

```bash
.venv/bin/python -m scripts.provision_admin create admin
.venv/bin/python -m scripts.provision_admin set-password admin
.venv/bin/python -m scripts.provision_admin disable admin
```

`RESIDENTS_COOKIE_SECURE` defaults to `true` and should remain enabled behind
HTTPS. Set it to `false` only for local HTTP development. The server requires
administrator sessions for all resident data and provides no public account
registration. Sessions expire after 30 minutes idle or 8 hours absolute; logout
and account disablement revoke server-side sessions.

`CORS_ORIGINS` must contain explicit trusted origins. The application rejects
`*` because authenticated requests use cookies and credentialed wildcard CORS
can expose responses to untrusted same-site origins. Configure only the
frontend's exact origin(s), including scheme and port.

`RESIDENTS_HSTS` should only be enabled when the application is reached over
HTTPS. HSTS can make a misconfigured HTTP deployment unreachable for the
configured duration.

`RESIDENTS_RATE_LIMIT_PER_MINUTE` applies an in-process sliding-window limit to
`/api/*`; `/health` is exempt. `RESIDENTS_TRUST_PROXY` controls whether
`X-Forwarded-For` is used for the rate-limit key. Only enable it when a trusted
reverse proxy overwrites that header; otherwise a direct client could spoof its
key. The limiter is local to one process, so use a reverse-proxy or platform
limit when running multiple instances.

`RESIDENTS_DB_INTEGRITY_CHECK` runs SQLite's `PRAGMA quick_check` before table
creation. A corrupt database prevents startup instead of serving unverified
data. A missing database is treated as healthy because startup creates it.

The request-size limit is enforced from the `Content-Length` header. A chunked
request without that header is not rejected by this check; keep an additional
body-size limit at the reverse proxy if that matters for your deployment.

`RESIDENTS_BACKUP_REQUIRED` controls the failure policy. The default (`false`)
logs a failed backup and allows the write to continue for availability. Set it
to `true` when a write must not proceed without a verified backup; the API then
returns `503`. Disabling backups makes this setting irrelevant.

### Test isolation

The pytest configuration sets these variables **before importing the app**:

- `RESIDENTS_DB_PATH` points to a temporary directory.
- `RESIDENTS_BACKUP_DIR` points inside the same temporary directory.
- `RESIDENTS_BACKUP_ENABLED` is `false`.
- `RESIDENTS_RATE_LIMIT_PER_MINUTE` is `0`; rate-limit tests enable it explicitly.
- `RESIDENTS_DB_INTEGRITY_CHECK` is `false`; integrity tests call the check
  directly.
- `RESIDENTS_COOKIE_SECURE` is set to `false` only because the isolated test client uses HTTP.

This prevents the test suite from creating, copying, or rotating the configured
application database and backups. Tests use synthetic data only. The temporary
directory is removed when the test process exits.

### Backups

On each create, update, or delete, the API calls `backup_database()` before the
write when backups are enabled. The backup uses SQLite's online backup API, not a
filesystem copy, so it captures a consistent snapshot while the database is open.

Backup behaviour:

- Files are named `residents_backup_<timestamp>_<microseconds>.db`.
- A collision suffix prevents overwriting an existing file.
- Each backup is checked with `PRAGMA quick_check`; a failed backup is removed
  and reported as unsuccessful.
- The newest 10 files are retained by default, ordered by the timestamped
  filename; configure with `RESIDENTS_BACKUP_RETENTION`.
- Failures are logged and do not block the write by default. Set
  `RESIDENTS_BACKUP_REQUIRED=true` for fail-closed behaviour.

Limitations:

- Backups remain on the same filesystem unless copied elsewhere operationally.
- The application does not encrypt backups or manage their permissions.
- No automated restore drill or backup-freshness alert is included.
- A pre-write backup protects against a bad write, but not against disk loss,
  host loss, or a compromised host.

See [operations.md](operations.md) for backup and restore procedures.

### Database pragmas and indexes

Every SQLite connection enables:

- `PRAGMA foreign_keys=ON`
- `PRAGMA busy_timeout=5000`
- `PRAGMA journal_mode=WAL`

`create_tables()` creates missing tables and indexes on startup. Existing
databases receive the search and foreign-key indexes through
`CREATE INDEX IF NOT EXISTS`. This is not a general schema-migration system; see
[operations.md](operations.md#schema-changes).

### Legacy HTML-escaped data

Older versions stored `html.escape` output. The current API stores raw text and
rejects `<`/`>` markup. Use the migration utility to report legacy values:

```bash
# Dry run: reports only; no writes and no backup
python scripts/migrate_unescape.py --db /path/to/residents.db

# Apply after reviewing the report; creates a verified backup first
python scripts/migrate_unescape.py --db /path/to/residents.db --apply
```

Run it against a copy or synthetic database first. Do not run it against a real
resident database without operational approval.

---

## Frontend

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `/api` | Base URL used by the Axios client |

Vite proxies `/api` to `http://localhost:8000` during `npm run dev` and
`npm run preview`. The default works without configuration.

Create `frontend/.env.local` (ignored by Git) or export the variable before
running Vite:

```bash
cd frontend
cp .env.example .env.local
# edit .env.local only for a split frontend/API deployment
npm ci
npm run dev
```

Vite only exposes variables prefixed with `VITE_` to client code. Do not put
secrets in frontend environment variables; they are bundled into the client.

The session cookie is HTTP-only; the client keeps only the CSRF token in memory and clears it on sign-out or a `401` response.

---

## Docker

The Dockerfile is multi-stage:

1. A Node stage installs frontend dependencies with `npm ci` from the tracked
   `frontend/package-lock.json` and runs `npm run build`.
2. A Python stage installs `requirements.txt`, copies the API, migration script,
   and built frontend, then runs as the non-root `app` user.
3. Data is stored under `/data` and declared as a volume.
4. A healthcheck calls `/health` on port 8000.

```bash
docker build -t residents-app .
docker run --rm -p 8000:8000 \
  -v residents-data:/data \
  -e RESIDENTS_COOKIE_SECURE=true \
  residents-app
```

`docker-compose.example.yml` provides a starting point.

**Verification status:** the image built locally and an isolated, ephemeral
container smoke test confirmed `/health` returns `200`, an unauthenticated
protected API returns `401`, a protected direct page redirects to `/login`,
`/login` returns `200`, and registration is not available (`405`). The backend
suite separately validates admin login and authenticated workflows. No real
resident data was used. An approved deployment still needs TLS, persistent
storage, external backups, and a restore drill.

Operational requirements for Docker:

- Terminate TLS at a reverse proxy; do not expose plain HTTP to untrusted
  networks.
- Persist `/data`; otherwise the database and backups disappear with the
  container.
- Run one application replica against one SQLite file.
- Copy backups off the host and test restoration.
- Provision admin accounts with `python -m scripts.provision_admin` using the persistent application database. Keep `RESIDENTS_COOKIE_SECURE=true` behind TLS.
- Set `CORS_ORIGINS` to the real frontend origin if it differs from the API
  origin.

---

## Verification commands

```bash
# Backend tests (isolated temporary DB; backups disabled)
.venv/bin/python -m pytest tests/ -v

# Coverage
.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing

# Frontend unit tests, lint, and production build
cd frontend
npm test
npm run lint
npm run build

# Backend development server
uvicorn app.main:app --reload
```

Do not run tests against a database containing real resident data.
