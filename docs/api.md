# API Reference

Base URL: `http://localhost:8000/api`

The React client uses `VITE_API_BASE_URL` when configured. Its default is `/api`,
which Vite proxies to `http://localhost:8000` in development and which the
backend serves directly in production. See [configuration.md](configuration.md).

Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## Authentication

Resident, reference-data, and audit endpoints always require an administrator
session. Accounts are provisioned by an operator; there is no registration API.

| Endpoint | Auth required | Purpose |
|---|---|---|
| `GET /api/auth/status` | No | Reports whether a valid administrator session exists and returns its CSRF token |
| `POST /api/auth/login` | No | Validates provisioned credentials and sets an HTTP-only session cookie |
| `POST /api/auth/logout` | Admin | Revokes the current server-side session and clears its cookie |
| `GET /api/auth/verify` | Admin | Confirms an authenticated administrator session |
| All other `/api/*` endpoints | Admin | Require a valid administrator session |

Successful login sets `residents_admin_session` with `HttpOnly`,
`SameSite=Strict`, and `Secure` by default. The API returns a CSRF token in the
response body; the client keeps it in memory and sends it as `X-CSRF-Token` on
non-read requests. Sessions expire after 30 minutes idle or 8 hours absolute.
Invalid sessions receive `401`; valid non-admin accounts receive `403`. Login
errors never establish a session. The SPA login shell at `/login` is public;
other page routes are checked server-side. `GET /health` remains public for
probes and exposes no resident data.

---

## Common headers

Every response includes baseline browser-security headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: camera=(), geolocation=(), microphone=()`
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-origin`
- `X-Permitted-Cross-Domain-Policies: none`
- `Content-Security-Policy` (conservative same-origin policy)
- `Strict-Transport-Security` only when `RESIDENTS_HSTS` is enabled

Every response also includes `X-Request-ID`. A well-formed caller-supplied
`X-Request-ID` (up to 64 alphanumeric, `-`, `_`, or `.` characters) is reused;
otherwise the server generates one. The value is recorded in write audit events
for correlation.

API and `/health` responses include `Cache-Control: no-store` so resident data
and health details are not cached by browsers or intermediaries.

Paged list and search responses include `X-Total-Count` with the total number of
matching rows before pagination. The header is exposed through CORS so a browser
client on a configured origin can read it.

---

## Rate limiting

`/api/*` requests are limited per client using an in-process sliding window.
The default is 300 requests per minute and is configurable with
`RESIDENTS_RATE_LIMIT_PER_MINUTE` (`0` disables it).

When the limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: <seconds>

{"detail": "Too many requests"}
```

`/health` is not rate-limited so probes continue to work. The limiter is local to
one process and is not a substitute for a reverse-proxy or platform rate limit.
`X-Forwarded-For` is only used when `RESIDENTS_TRUST_PROXY=true`; otherwise the
direct socket address is used.

---

## Villages

### `GET /villages`

Returns the list of all available villages.

**Response `200`**

```json
["Village A", "Village B", "Village C", "Village D"]
```

---

## Qualifications

### `GET /qualifications`

Returns all qualification reference data used to populate form dropdowns.

**Response `200`**

```json
{
  "types": ["Certificate", "Diploma", "..."],
  "fields": ["Agriculture", "Information Technology", "..."],
  "levels": ["NQF Level 1 ...", "NQF Level 10 ..."],
  "names": {
    "Information Technology": ["Computer Science", "Web Development", "..."]
  }
}
```

---

## Residents

### `GET /residents`

Returns residents with their qualifications, experiences, and skills. Optional
filters are combined with **AND**; residents matching several child rows still
appear once. The endpoint remains administrator-only.

**Query params**

| Param | Type | Default | Limits | Description |
|---|---|---|---|---|
| `limit` | integer | `100` | `1`–`500` | Maximum rows returned |
| `offset` | integer | `0` | `>= 0` | Rows to skip |
| `name` | string | omitted | max 200 chars | Case-insensitive partial match in first **or** last name |
| `village` | string | omitted | max 200 chars | Case-insensitive partial match in village |
| `qualification` | string | omitted | max 200 chars | Case-insensitive partial match in qualification name; known qualification fields are mapped to their names as in `/search` |
| `skill` | string | omitted | max 200 chars | Case-insensitive partial match in skill name |
| `sort_by` | string | `id` | `id`, `first_name`, `last_name`, `village`, `dob` | Primary sort field |
| `sort_order` | string | `asc` | `asc`, `desc` | Primary sort direction |

Omitted or blank filters are ignored. `%` and `_` in filter values are treated
literally. Sorting always has a deterministic resident-ID tie-breaker: ID is
ascending when another field is selected; when sorting by ID, `sort_order`
controls the ID direction. Invalid sort fields, directions, overlong filters,
or pagination values return `422`. The returned total counts all matching
residents before pagination.

**Response `200`** — array of resident objects

**Response headers** — `X-Total-Count: <total matching residents>`

**Response `422`** — invalid filters, sort parameters, or pagination values

The browser's browse and search views share this filtered endpoint. Applying
filters starts at the first page; reset clears all filters, sorting, and page
state. Changing sort also returns to the first page. The separate `/search`
endpoint below remains available for existing single-category clients.

---

### `GET /residents/{id}`

Returns a single resident by ID.

**Path params**

| Param | Type | Description |
|---|---|---|
| `id` | integer | Resident ID |

**Response `200`** — resident object
**Response `404`** — `{ "detail": "Resident not found" }`

---

### `POST /residents`

Creates a new resident.

**Request body**

```json
{
  "first_name": "Mpho",
  "last_name": "Mogowane",
  "dob": "1990-01-01",
  "gender": "Male",
  "village": "Village A",
  "cellphone_no": "0821234567",
  "cellphone_no2": null,
  "email": "mpho@example.com",
  "qualifications": [
    {
      "institution": "UNISA",
      "name": "Software Engineering",
      "type": "Degree",
      "level": "NQF Level 7 (Bachelor's Degree / Advanced Diploma)",
      "year": "2015"
    }
  ],
  "experiences": [
    { "company": "Acme Corp", "position": "Developer", "years": "3" }
  ],
  "skills": [
    { "name": "Python" }
  ]
}
```

**Validation**

| Field | Rule |
|---|---|
| `first_name`, `last_name` | Required, 1–100 characters after trimming |
| `gender`, `village` | Required, 1–100 characters after trimming |
| `cellphone_no` | Required, 1–30 characters after trimming |
| `cellphone_no2` | Optional, max 30 characters; blank becomes `null` |
| `email` | Optional valid email, max 254 characters; blank becomes `null` |
| `dob` | Required ISO 8601 date; future dates rejected |
| `qualifications` | At most 50 rows |
| `experiences` | At most 50 rows |
| `skills` | At most 50 rows |
| Child text fields | Required after trimming; `institution`, `name`, `type`, `level`, `company`, `position` max 200; `year`, `years` max 20; skill `name` max 100 |
| All text fields | `<` and `>` are rejected as HTML markup; values are otherwise stored as raw text |

Optional blank strings are normalised to `null`. Values are trimmed before
storage. Markup is rejected rather than persisted in escaped form; React escapes
all rendered text.

**Response `201`** — created resident object
**Response `413`** — request body exceeds `RESIDENTS_MAX_REQUEST_BYTES`
**Response `422`** — validation error details
**Response `503`** — an enabled, required pre-write backup failed
(`RESIDENTS_BACKUP_REQUIRED=true`)

---

### `PUT /residents/{id}`

Replaces mutable data for an existing resident. Existing qualifications,
experiences, and skills are deleted and replaced with the submitted data.

Identity fields are immutable through this endpoint:

- `first_name`
- `last_name`
- `dob`
- `gender`
- `village`

**Path params**

| Param | Type | Description |
|---|---|---|
| `id` | integer | Resident ID |

**Request body** — same schema as `POST /residents`, with unchanged identity
fields.

**Response `200`** — updated resident object
**Response `404`** — resident not found
**Response `409`** — one or more identity fields differ; the detail lists them
**Response `413`** — request body too large
**Response `422`** — validation error
**Response `503`** — an enabled, required pre-write backup failed

The response audit event records which contact field names changed, but never
their values.

The add/edit forms associate validation locations with the corresponding
personal-detail or nested-record field, announce a concise error summary, and
retain entered values after a rejected submission. Successful saves navigate
back to the resident list with a success message.

---

### `DELETE /residents/{id}`

Permanently deletes a resident and all related records. The frontend requires an
explicit confirmation before calling this endpoint.

**Response `204`** — no content
**Response `404`** — resident not found
**Response `503`** — an enabled, required pre-write backup failed

There is no soft-delete or undo. A pre-write backup is created when backups are
enabled, and a non-PII `delete` audit event is retained after the resident row is
removed.

---

## Search

### `GET /search`

Searches residents by one selected criterion. This existing endpoint and its
`search_type` parameter are retained for single-category clients; the browser
uses the combined filters on `GET /residents`.

**Query params**

| Param | Type | Default | Description |
|---|---|---|---|
| `query` | string | `""` | Search term, max 200 characters |
| `search_type` | string | `"name"` | `name`, `village`, `qualification`, or `skill` |
| `limit` | integer | `100` | `1`–`500` |
| `offset` | integer | `0` | `>= 0` |

**Behaviour**

- `name` matches first name or last name, case-insensitively.
- `village` matches the village, case-insensitively.
- `qualification` accepts either a qualification **field** (for example,
  `Information Technology`) or a qualification **name** (for example,
  `Software Engineering`). Field values are mapped to their known names using
  `app/qualifications.py`.
- `skill` matches skill names, case-insensitively.
- `%` and `_` in the query are treated literally, not as SQL wildcards.
- A blank query returns `[]` with `X-Total-Count: 0`.
- Results are ordered by resident ID and de-duplicated.

**Response `200`** — array of matching resident objects
**Response headers** — `X-Total-Count: <total matches>`
**Response `422`** — query too long or unknown `search_type`

**Examples**

```
GET /api/search?query=Mpho&search_type=name
GET /api/search?query=Village+A&search_type=village
GET /api/search?query=Information+Technology&search_type=qualification
GET /api/search?query=Software+Engineering&search_type=qualification
GET /api/search?query=Python&search_type=skill
GET /api/search?query=Mpho&search_type=name&limit=20&offset=40
```

---

## Audit trail

### `GET /audit`

Returns non-PII write events, newest first. The endpoint requires the same
authentication as the rest of `/api/*`.

**Query params**

| Param | Type | Default | Description |
|---|---|---|---|
| `action` | string | all | `create`, `update`, or `delete` |
| `resident_id` | integer | all | Filter by resident ID (`>= 1`) |
| `limit` | integer | `100` | `1`–`500` |
| `offset` | integer | `0` | `>= 0` |

**Response `200`** — array of audit events

```json
[
  {
    "id": 3,
    "created_at": "2026-11-02T08:45:00Z",
    "action": "update",
    "resident_id": 1,
    "actor": "shared-token",
    "request_id": "3d2e6587188e49e6a891ecea936db525",
    "detail": "contact_fields=email,cellphone_no"
  }
]
```

**Privacy:**

- No resident names, phone numbers, email addresses, or field values are stored.
- `actor` is `shared-token` when authentication is configured, otherwise
  `anonymous`.
- The token itself is never stored.
- There is no foreign key from `audit_events` to `residents`, so delete events
  survive removal of the resident.
- Events are retained indefinitely until an operator defines a retention or
  export policy; there is no audit UI.

**Response headers** — `X-Total-Count: <total matching events>`

---

## Health

### `GET /health`

Public liveness/readiness endpoint. It executes `SELECT 1` against the configured
database.

**Response `200`**

```json
{"status": "ok", "database": "ok"}
```

**Response `503`**

```json
{"status": "error", "database": "unavailable"}
```

The endpoint does not return resident data, counts, or configuration.

---

## Resident Object Schema

```json
{
  "id": 1,
  "first_name": "Mpho",
  "last_name": "Mogowane",
  "dob": "1990-01-01",
  "gender": "Male",
  "village": "Village A",
  "cellphone_no": "0821234567",
  "cellphone_no2": null,
  "email": "mpho@example.com",
  "qualifications": [
    {
      "id": 1,
      "institution": "UNISA",
      "name": "Software Engineering",
      "type": "Degree",
      "level": "NQF Level 7 (Bachelor's Degree / Advanced Diploma)",
      "year": "2015"
    }
  ],
  "experiences": [
    { "id": 1, "company": "Acme Corp", "position": "Developer", "years": "3" }
  ],
  "skills": [
    { "id": 1, "name": "Python" }
  ]
}
```

---

## Error format

FastAPI returns validation errors as an array:

```json
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "first_name"],
      "msg": "String should have at most 100 characters",
      "input": "..."
    }
  ]
}
```

The React client normalises both string and array `detail` values into a readable
message. Unexpected server errors return a generic message and do not include
exception details.
