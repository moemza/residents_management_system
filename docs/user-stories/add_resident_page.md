# Add Resident Page – User Stories

## Epic: Add New Resident

**As a system user (admin or data capturer),**  
I want to add a new resident with personal, education, work experience, and skills information,  
So that resident data is accurately stored and managed in the system.

---

## Personal Details

### US-01: Capture basic personal information
**As a user**  
I want to enter a resident’s first name, last name, date of birth, and gender  
So that the resident can be uniquely identified.

**Acceptance Criteria**
- First name is required
- Last name is required
- Date of birth is required and follows `YYYY-MM-DD` format
- Gender must be selected from a predefined list
- Form cannot be submitted if required fields are missing

---

### US-02: Assign resident to a village
**As a user**  
I want to select a village from a predefined list  
So that the resident is linked to the correct community.

**Acceptance Criteria**
- Village list is populated from the system
- Village selection is mandatory
- Empty village selection is not allowed

---

### US-03: Capture resident contact details
**As a user**  
I want to enter one or two cellphone numbers and an optional email address  
So that the resident can be contacted when needed.

**Acceptance Criteria**
- Primary cellphone number is required
- Secondary cellphone number is optional
- Email is optional
- Email must be valid if provided

---

## Education

### US-04: Capture education details
**As a user**  
I want to add education details for a resident  
So that their qualifications are recorded.

**Acceptance Criteria**
- Institution name can be entered
- Qualification name must be selected from a grouped list
- Qualification type is required
- Qualification level is required
- Year can be entered manually

---

### US-05: Add multiple education records
**As a user**  
I want to add multiple education entries  
So that all qualifications can be captured.

**Acceptance Criteria**
- Clicking **+ Add** creates a new education row
- Multiple education rows can be added
- All rows are submitted together

---

### US-06: Remove an education record
**As a user**  
I want to remove an education entry  
So that incorrect or unnecessary data is not saved.

**Acceptance Criteria**
- Clicking the delete (✖) button removes the selected education row
- Remaining rows are unaffected

---

## Work Experience

### US-07: Capture work experience
**As a user**  
I want to add work experience details  
So that the resident’s employment history is recorded.

**Acceptance Criteria**
- Company name can be entered
- Position can be entered
- Years of experience can be entered

---

### US-08: Add multiple work experience records
**As a user**  
I want to add more than one work experience entry  
So that a full employment history can be captured.

**Acceptance Criteria**
- Clicking **+ Add** creates a new work experience row
- Multiple rows can be added
- All rows are submitted together

---

### US-09: Remove a work experience record
**As a user**  
I want to remove a work experience entry  
So that incorrect data can be corrected before saving.

**Acceptance Criteria**
- Clicking delete removes only the selected row

---

## Skills

### US-10: Capture resident skills
**As a user**  
I want to enter a list of skills for a resident  
So that their abilities are documented.

**Acceptance Criteria**
- Skill field accepts free text
- At least one skill row is available by default

---

### US-11: Add and remove skills
**As a user**  
I want to dynamically add or remove skills  
So that the skills list accurately reflects the resident.

**Acceptance Criteria**
- Clicking **+ Add** creates a new skill row
- Clicking delete removes the selected skill row

---

## Save Resident

### US-12: Save resident details
**As a user**  
I want to submit the form and save the resident’s information  
So that it is stored in the system for future use.

**Acceptance Criteria**
- Form submits successfully when all required fields are valid
- Resident data is persisted in the database
- User receives confirmation that the resident was saved

---
