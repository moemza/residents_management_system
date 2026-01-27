# Edit Resident Page – User Stories

## Epic: Edit Resident Information

**As a system user (admin or data capturer),**  
I want to view and edit an existing resident’s information,  
So that resident records remain accurate and up to date.

---

## View Existing Resident Details

### US-ER-01: View resident details for editing
**As a user**  
I want to see a resident’s existing personal, education, experience, and skills information pre-filled in the form  
So that I can easily review and update their details.

**Acceptance Criteria**
- Resident personal details are pre-populated
- Existing education records are displayed
- Existing work experience records are displayed
- Existing skills are displayed
- Resident name is shown in the page heading

---

## Personal Details

### US-ER-02: Edit personal information
**As a user**  
I want to edit a resident’s personal details  
So that incorrect or outdated information can be corrected.

**Acceptance Criteria**
- First name and last name are editable and required
- Date of birth is editable and required
- Gender can be changed using a dropdown
- Form validation prevents submission if required fields are empty

---

### US-ER-03: Update village and contact details
**As a user**  
I want to update a resident’s village and contact information  
So that their location and contact details remain current.

**Acceptance Criteria**
- Village list is populated from the system
- Current village is pre-selected
- Primary cellphone number is required
- Secondary cellphone number is optional
- Email is optional but must be valid if provided

---

## Education

### US-ER-04: View existing education records
**As a user**  
I want to see all existing education records for a resident  
So that I can review their qualifications.

**Acceptance Criteria**
- All saved education entries are displayed
- Fields are pre-filled with existing data
- Qualification name, type, and level are selected correctly

---

### US-ER-05: Edit education records
**As a user**  
I want to edit existing education entries  
So that qualification information can be updated.

**Acceptance Criteria**
- Institution, qualification name, type, level, and year are editable
- Changes are saved when the form is submitted

---

### US-ER-06: Add new education records
**As a user**  
I want to add new education entries while editing a resident  
So that newly obtained qualifications can be captured.

**Acceptance Criteria**
- Clicking **+ Add** creates a new education row
- New rows behave the same as existing rows
- New education entries are saved on submission

---

### US-ER-07: Remove an education record
**As a user**  
I want to remove an education entry  
So that incorrect or irrelevant qualifications are not saved.

**Acceptance Criteria**
- Clicking delete (✖) removes the selected education row
- Remaining rows are unaffected

---

## Work Experience

### US-ER-08: View and edit work experience
**As a user**  
I want to view and edit a resident’s work experience  
So that their employment history stays accurate.

**Acceptance Criteria**
- Existing work experience entries are displayed
- Company, position, and years fields are editable

---

### US-ER-09: Add and remove work experience entries
**As a user**  
I want to add or remove work experience entries  
So that the resident’s employment history reflects reality.

**Acceptance Criteria**
- Clicking **+ Add** creates a new experience row
- Clicking delete removes only the selected experience row
- All changes are saved on submission

---

## Skills

### US-ER-10: View and edit skills
**As a user**  
I want to view and update a resident’s skills  
So that their abilities are accurately documented.

**Acceptance Criteria**
- Existing skills are pre-filled
- Skill values are editable
- Skills accept free text

---

### US-ER-11: Add and remove skills
**As a user**  
I want to add or remove skills dynamically  
So that the skills list matches the resident’s capabilities.

**Acceptance Criteria**
- Clicking **+ Add** creates a new skill row
- Clicking delete removes the selected skill
- Updated skill list is saved on submission

---

## Save Changes

### US-ER-12: Update resident details
**As a user**  
I want to submit the edited resident information  
So that changes are saved in the system.

**Acceptance Criteria**
- Form submits successfully when validation passes
- Updated data replaces previous resident data
- User remains on a valid page after submission

---

## Navigation

### US-ER-13: Return to home
**As a user**  
I want to return to the home page from the Edit Resident screen  
So that I can continue working elsewhere in the system.

**Acceptance Criteria**
- Home button navigates back to the home page
