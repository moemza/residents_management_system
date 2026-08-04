# API Reference

Base URL: `http://localhost:8000/api`

Interactive docs (Swagger UI): `http://localhost:8000/docs`

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
  "types": ["Certificate", "Diploma", ...],
  "fields": ["Agriculture", "Information Technology", ...],
  "levels": ["NQF Level 1 ...", "NQF Level 10 ...", ...],
  "names": {
    "Information Technology": ["Computer Science", "Web Development", ...],
    ...
  }
}
```

---

## Residents

### `GET /residents`

Returns all residents with their qualifications, experiences, and skills.

**Response `200`** — array of resident objects (see schema below)

---

### `GET /residents/{id}`

Returns a single resident by ID.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
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
- `first_name`, `last_name`, `gender`, `village`, `cellphone_no` — required, sanitized
- `dob` — required, ISO 8601 date (`YYYY-MM-DD`)
- `email` — optional, must be a valid email if provided
- `cellphone_no2` — optional, sanitized if provided

**Response `201`** — created resident object  
**Response `422`** — validation error details

---

### `PUT /residents/{id}`

Replaces all data for an existing resident. Existing qualifications, experiences, and skills are deleted and replaced with the submitted data.

**Path params**
| Param | Type | Description |
|-------|------|-------------|
| `id` | integer | Resident ID |

**Request body** — same schema as `POST /residents`

**Response `200`** — updated resident object  
**Response `404`** — resident not found  
**Response `422`** — validation error

---

### `DELETE /residents/{id}`

Deletes a resident and all related records.

**Response `204`** — no content  
**Response `404`** — resident not found

---

## Search

### `GET /search`

Searches residents by a given criteria.

**Query params**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | `""` | Search term |
| `search_type` | string | `"name"` | One of: `name`, `village`, `qualification`, `skill` |

Returns an empty array if `query` is blank.

**Response `200`** — array of matching resident objects

**Examples**
```
GET /api/search?query=Mpho&search_type=name
GET /api/search?query=Village+A&search_type=village
GET /api/search?query=Information+Technology&search_type=qualification
GET /api/search?query=Python&search_type=skill
```

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
