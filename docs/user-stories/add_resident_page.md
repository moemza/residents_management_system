# Add Resident Page – User Stories

## Epic: Add New Resident

**As a system user,**  
I want to add a new resident with personal, education, work experience, and skills information,  
so that resident data is accurately stored and managed in the system.

---

## Personal Details

### US-01: Capture basic personal information
**As a user**  
I want to enter a resident's first name, last name, date of birth, and gender  
so that the resident can be uniquely identified.

**Acceptance Criteria**
- First name and last name are required — inline error shown if blank on submit
- Date of birth is required, uses a native date picker, and cannot be a future date
- Gender must be selected from: Male, Female, Other
- Form cannot be submitted if required fields are missing

---

### US-02: Assign resident to a village
**As a user**  
I want to select a village from a dropdown populated from the API  
so that the resident is linked to the correct community.

**Acceptance Criteria**
- Village list is fetched from `GET /api/villages` on page load
- Village selection is required — inline error shown if not selected on submit

---

### US-03: Capture contact details
**As a user**  
I want to enter one or two cellphone numbers and an optional email address  
so that the resident can be contacted.

**Acceptance Criteria**
- Primary cellphone number is required
- Secondary cellphone number is optional
- Email is optional but must pass format validation if provided
- Invalid email shows an inline error message

---

## Education

### US-04: Add education records
**As a user**  
I want to add one or more education entries  
so that a resident's qualifications are recorded.

**Acceptance Criteria**
- Clicking **+ Add** appends a new education row
- Each row has: Institution (text), Name (grouped dropdown), Type (dropdown), Level (dropdown), Year (text)
- Dropdown options are fetched from `GET /api/qualifications`
- Clicking ✖ removes that row without affecting others

---

## Work Experience

### US-05: Add work experience records
**As a user**  
I want to add one or more work experience entries  
so that a resident's employment history is recorded.

**Acceptance Criteria**
- Clicking **+ Add** appends a new experience row
- Each row has: Company, Position, Years
- Clicking ✖ removes that row

---

## Skills

### US-06: Add skills
**As a user**  
I want to add a list of free-text skills  
so that a resident's abilities are documented.

**Acceptance Criteria**
- Clicking **+ Add** appends a new skill input
- Clicking ✖ removes that skill
- Skills accept any free text

---

## Save

### US-07: Submit the form
**As a user**  
I want to submit the form and be redirected to the home page with a confirmation  
so that I know the resident was saved successfully.

**Acceptance Criteria**
- On valid submission, `POST /api/residents` is called
- User is redirected to `/` with a success toast notification
- On API error, an inline error toast is shown and the user stays on the form
- The submit button shows "Saving…" and is disabled while the request is in flight
