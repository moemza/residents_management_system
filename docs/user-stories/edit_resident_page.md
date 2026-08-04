# Edit Resident Page – User Stories

## Epic: Edit Resident Information

**As a system user,**  
I want to view and edit an existing resident's information,  
so that resident records remain accurate and up to date.

---

## Load Existing Data

### US-ER-01: Pre-populate form with existing data
**As a user**  
I want to see a resident's existing information pre-filled when I open the edit page  
so that I can review and update only what has changed.

**Acceptance Criteria**
- Page calls `GET /api/residents/{id}` on load
- A loading spinner is shown while data is fetching
- If the resident is not found, an error message is shown
- All personal, education, experience, and skill fields are pre-populated

---

## Personal Details

### US-ER-02: Read-only identity fields
**As a user**  
I want first name, last name, date of birth, gender, and village to be read-only  
so that core identity data cannot be accidentally changed.

**Acceptance Criteria**
- First name, last name, dob, gender, and village are displayed as read-only inputs
- These values are still submitted as part of the update payload

---

### US-ER-03: Edit contact details
**As a user**  
I want to update cellphone numbers and email  
so that contact information stays current.

**Acceptance Criteria**
- Primary cellphone is required — inline error if blank on submit
- Secondary cellphone is optional
- Email is optional but validated if provided

---

## Education, Experience, Skills

### US-ER-04: Edit existing records
**As a user**  
I want all existing education, experience, and skill entries to be pre-filled and editable  
so that I can correct or update them.

**Acceptance Criteria**
- All existing rows are rendered with their saved values
- Any field in any row can be changed

---

### US-ER-05: Add and remove rows
**As a user**  
I want to add new rows or remove existing ones  
so that the resident's records reflect reality.

**Acceptance Criteria**
- Clicking **+ Add** appends a blank row to any section
- Clicking ✖ removes that row
- On save, the full updated set of rows replaces the previous data

---

## Save

### US-ER-06: Submit changes
**As a user**  
I want to submit the form and be redirected to the home page with a confirmation  
so that I know the update was saved.

**Acceptance Criteria**
- On valid submission, `PUT /api/residents/{id}` is called
- User is redirected to `/` with a success toast notification
- On API error, an inline error toast is shown and the user stays on the form
- The submit button shows "Saving…" and is disabled while the request is in flight
