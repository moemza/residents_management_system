# Operations Guide

This guide covers deployment, health checks, backups, restoration, migrations,
administrator account lifecycle, monitoring, and known operational limits. It does not authorise
changes to production systems or real resident data. Use synthetic data for
drills.

---

## Deployment topology

Recommended minimum for a single-host deployment:

```
Internet ──► TLS reverse proxy ──► FastAPI/uvicorn (one instance)
                                      │
                                      └──► SQLite file + backups on a persistent volume
```

- Terminate TLS at a reverse proxy (nginx, Caddy, a managed load balancer, or
  equivalent). Do not expose plain HTTP to untrusted networks.
- Run **one** application process or replica against a SQLite file. SQLite is
  single-writer; multiple writers across hosts are not supported.
- Put the database and backups on a persistent volume, not inside an ephemeral
  container layer.
- Provision administrator accounts with the operator CLI against the application database; never use public registration.
- Set `CORS_ORIGINS` to the exact browser origin(s) if the frontend is served
  from a different origin than the API.
- Enable `RESIDENTS_HSTS=true` only after HTTPS is working correctly.

The Dockerfile runs as a non-root user, stores data in `/data`, and exposes port
8000 with a `/health` healthcheck. The image was built and smoke-tested locally
with a temporary volume and synthetic data; see
[configuration.md](configuration.md#docker). It still needs validation in an
approved deployment environment with TLS and persistent storage.

---

## Pre-deployment checklist

- [ ] Database and backup paths point to persistent, access-controlled storage.
- [ ] At least one administrator account has been provisioned and its credentials are stored securely.
- [ ] `RESIDENTS_COOKIE_SECURE=true` is retained behind HTTPS.
- [ ] `RESIDENTS_RATE_LIMIT_PER_MINUTE` and `RESIDENTS_TRUST_PROXY` match the
      reverse-proxy layout.
- [ ] `RESIDENTS_BACKUP_REQUIRED` and `RESIDENTS_BACKUP_RETENTION` match the
      recovery policy.
- [ ] `RESIDENTS_DB_INTEGRITY_CHECK` remains enabled unless a documented
      exception exists.
- [ ] TLS is terminated by a trusted reverse proxy.
- [ ] `CORS_ORIGINS` contains only intended origins.
- [ ] `RESIDENTS_HSTS` is enabled only for HTTPS deployments.
- [ ] Backups are copied off-host and a restore drill has been completed on
      synthetic data.
- [ ] Log aggregation does not record query strings or request bodies containing
      resident data.
- [ ] Disk-space and backup-freshness alerts are configured.
- [ ] The frontend build is current (`npm run build`) and served from the same
      origin or a configured `VITE_API_BASE_URL`.
- [ ] The deployment has an owner-approved retention and deletion policy.

---

## Health checks

`GET /health` is public and returns:

```json
{"status": "ok", "database": "ok"}
```

It executes `SELECT 1` against the configured database and returns `503` if the
database is unavailable. It does not return resident counts or configuration.

On startup, the application runs `PRAGMA quick_check` before creating missing
tables and indexes when `RESIDENTS_DB_INTEGRITY_CHECK=true` (the default). A
corrupt database prevents startup; inspect the process log for the critical
message rather than repeatedly restarting.

Use it for:

- container healthchecks;
- load-balancer readiness probes;
- uptime monitoring.

Do not use it as a substitute for backup-freshness, disk-space, or application
error-rate monitoring. It is exempt from the application rate limit.

---

## Backups

### Automatic backups

When `RESIDENTS_BACKUP_ENABLED` is true (the default), the API creates a
pre-write snapshot before each create, update, or delete.

- Uses SQLite's online backup API for a consistent snapshot.
- Verifies the snapshot with `PRAGMA quick_check`.
- Stores files in `RESIDENTS_BACKUP_DIR`.
- Retains the newest 10 by timestamped filename by default; configure with
  `RESIDENTS_BACKUP_RETENTION`.
- Logs failures and does not block the write by default.
- Set `RESIDENTS_BACKUP_REQUIRED=true` to abort a write with `503` when an
  enabled backup fails. Fail-closed protects against unprotected writes at the
  cost of availability; choose deliberately.

The application never writes to the configured database or rotates backups during
tests; the test suite uses a temporary directory.

### Manual backup

Use SQLite's backup API rather than copying a live database file. Example with
Python's standard library (review paths before running):

```bash
python - <<'PY'
import sqlite3
from pathlib import Path

source = Path("/data/residents.db")
destination = Path("/data/backups/manual_residents.db")
destination.parent.mkdir(parents=True, exist_ok=True)

src = sqlite3.connect(source)
dst = sqlite3.connect(destination)
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()

check = sqlite3.connect(destination)
try:
    print(check.execute("PRAGMA quick_check").fetchone())
finally:
    check.close()
PY
```

Copy completed backups off the host to storage with appropriate access controls
and retention. The application does not encrypt backups.

### Restore drill

Perform this on a **synthetic** database or an isolated environment:

1. Stop the application so no writes occur.
2. Preserve the current database file; do not overwrite it in place.
3. Verify the backup:
   ```bash
   sqlite3 /path/to/backup.db 'PRAGMA quick_check;'
   ```
   Expect `ok`.
4. Copy the verified backup to the configured `RESIDENTS_DB_PATH` on an isolated
   host or after explicit approval.
5. Start the application and check `/health`.
6. Read a synthetic record through the API and confirm expected values.
7. Record the drill date, backup used, result, and any data loss window.

A backup that has never been restored is not a verified recovery mechanism.

---

## Rate limiting and request correlation

The API applies an in-process sliding-window limit to `/api/*`:

- default: 300 requests per minute per client;
- configure with `RESIDENTS_RATE_LIMIT_PER_MINUTE`;
- `0` disables the limiter;
- excess requests return `429` with `Retry-After`;
- `/health` is exempt so probes keep working.

By default the key is the direct socket address. Set `RESIDENTS_TRUST_PROXY=true`
only when a trusted reverse proxy overwrites `X-Forwarded-For`; otherwise a
direct client can spoof its key.

Limitations:

- State is in memory and resets on restart.
- The limit is per process, not shared across replicas.
- It is not a brute-force lockout or a substitute for a proxy/platform limit.
- Run one process per SQLite file, so per-process state currently matches the
  deployment.

Every response includes `X-Request-ID`. A well-formed caller value is reused;
otherwise a 32-character ID is generated. Write audit events record the ID,
which lets an operator correlate a report with an audit row without storing
resident data. Do not treat the ID as a secret.

---

## Audit trail

Create, update, and delete operations append an `audit_events` row in the same
transaction as the write:

- action (`create`, `update`, `delete`);
- resident ID;
- administrator username;
- request ID;
- for updates, changed contact field names only.

It never stores names, phone numbers, email addresses, or field values. There is
no foreign key to `residents`, so delete events
survive resident removal. Read access is not audited.

`GET /api/audit` returns events newest first with `action`, `resident_id`,
`limit`, and `offset` filters. There is no audit UI, retention job, export, or
tamper-evident storage. Define a retention and access policy before production
use.

---

## Legacy HTML-entity migration

Older versions persisted `html.escape` output. The current API stores raw text
and rejects `<`/`>` markup. Use the migration utility on a copy first:

```bash
# Report only; no writes and no backup
python scripts/migrate_unescape.py --db /path/to/copy.db

# Review the output, then apply; a verified backup is created first
python scripts/migrate_unescape.py --db /path/to/copy.db --apply
```

The utility:

- only touches an explicit allow-list of text columns;
- defaults to dry-run;
- creates and integrity-checks a pre-migration backup before writing;
- updates in a single transaction;
- is idempotent.

Do not run it against a real resident database without operational approval.
Values that become markup after unescaping are stored as raw text; React escapes
them at render time, and the API rejects new markup.

---

## Schema changes

`create_tables()` creates missing tables and indexes. It does **not** alter
existing columns or migrate data. For schema changes:

1. Design the change and its rollback.
2. Test it against a synthetic copy.
3. Take a verified backup.
4. Apply through a reviewed migration script or manual procedure.
5. Verify `/health`, indexes, foreign keys, and representative reads.
6. Record the change and rollback steps.

Do not rely on `create_all()` to evolve production schemas.

---

## Administrator account lifecycle

Provision accounts from the operator environment using the same persistent
`RESIDENTS_DB_PATH` as the application:

```bash
python -m scripts.provision_admin create admin-name
python -m scripts.provision_admin set-password admin-name
python -m scripts.provision_admin disable admin-name
```

The CLI prompts for passwords; do not pass them as command-line arguments.
Changing a password or disabling an account revokes that account's server-side
sessions. There is no public registration or administrator-management API.
Keep `RESIDENTS_COOKIE_SECURE=true` behind TLS; set it to `false` only for local
HTTP development. Sessions expire after 30 minutes idle or 8 hours absolute.

## Logging and privacy

- The global exception handler logs the request path, exception type, and stack
  frames, but not the query string or exception message.
- Uvicorn/proxy access logs may still record paths and query strings. Configure
  them to avoid search terms or request bodies, or restrict access to logs.
- Do not log request bodies, session cookies, passwords, CSRF values, or resident records.
- Keep logs on access-controlled storage with a defined retention period.

---

## Monitoring

At minimum, monitor:

- `/health` availability and latency;
- HTTP 5xx rate and `429` rate;
- authentication failure rate;
- disk space for the database, WAL files, and backups;
- backup creation failures and backup age;
- startup integrity-check failures;
- application restarts and deployment changes.

Alert when backups are older than the agreed recovery point objective (RPO) or
when disk space is low. The application does not expose metrics, send alerts, or
provide a metrics endpoint. Use request IDs from responses and logs when
correlating incidents.

---

## Scaling and availability

Current design limits:

- SQLite is single-writer; run one application instance per database file.
- There is no built-in horizontal scaling, job queue, or read replica.
- WAL improves local concurrency but does not make multi-host writes safe.
- Admin sessions are stored in the application database, so a restart does not
  invalidate them; account disablement, password change, or logout revokes them.
- Rate limiting is in-process and resets on restart; there is no distributed
  limiter, circuit breaker, or retry policy.
- Audit events are stored in the same SQLite database and grow indefinitely.

If multi-instance or high-availability operation is required, migrate to a
server-grade database and add shared rate-limit/audit infrastructure as a
separate, reviewed project.

---

## Incident response

1. Preserve evidence and logs; do not delete the database or backups.
2. If administrator credentials may be exposed, use the operator CLI to set a new password (which revokes sessions) and review access
   logs.
3. If data integrity is in doubt, stop writes and restore from a verified backup
   in an isolated environment first.
4. If personal data may have been exposed, follow the organisation's privacy
   incident process; do not copy resident data into tickets or chat.
5. Record the timeline, impact, containment, recovery, and follow-up actions.

---

## Verification commands

```bash
# Backend tests (isolated temporary DB; backups disabled)
.venv/bin/python -m pytest tests/ -q

# Coverage
.venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing -q

# Frontend tests, lint, build, and dependency audit
cd frontend
npm ci
npm test
npm run lint
npm run build
npm audit

# Health check against a running instance
curl -fsS http://127.0.0.1:8000/health
```

Latest local verification: **179 backend tests passed**, **92% backend
coverage**, **9 frontend tests passed**, lint clean, production build passed,
`npm audit` reported **0 vulnerabilities**, and the Docker image passed a
temporary-volume smoke test. See
[gap-register.md](gap-register.md#verification-record).

Do not run tests, migrations, or restore drills against real resident data
without explicit approval and an isolated copy.
