# Search Resident Page – User Stories

## Epic: Search and Filter Residents

**As a system user (admin or data capturer),**  
I want to search for residents using names or surnames and apply filters,  
So that I can quickly and accurately find resident records that meet specific requirements.

---

## Search Criteria

### US-SR-01: Search by name or surname
**As a user**  
I want to search for a resident using a name or surname  
So that I can locate residents using basic identifying information.

**Acceptance Criteria**
- Search input accepts first name or surname
- Search input is required
- Partial matches are allowed
- Search is case-insensitive

---

### US-SR-02: Validate allowed search inputs
**As a user**  
I want the system to restrict searches to valid criteria  
So that search results are accurate and meaningful.

**Acceptance Criteria**
- Search does not accept empty input
- Search rejects unsupported identifiers if entered alone
- User is informed when input does not meet search requirements

---

## Filtering Functionality

### US-SR-03: Filter search results
**As a user**  
I want to filter resident search results  
So that I can narrow down results based on specific requirements.

**Acceptance Criteria**
- User can apply one or more filters
- Filters are optional and can be combined with search
- Filters refine results without requiring a new page

---

### US-SR-04: Filter by village
**As a user**  
I want to filter residents by village  
So that I can view residents from a specific location.

**Acceptance Criteria**
- Village filter is available
- Only residents from the selected village are displayed
- Filter works together with name/surname search

---

### US-SR-05: Filter by status or requirement
**As a user**  
I want to filter residents based on predefined requirements or status  
So that I can find residents that meet specific criteria.

**Acceptance Criteria**
- Requirement/status filter options are clearly labeled
- Only residents matching the selected requirement are displayed
- Filter selection can be changed or cleared

---

## Search Results

### US-SR-06: View filtered search results
**As a user**  
I want to view search results that reflect both my search input and filters  
So that I can identify the correct resident quickly.

**Acceptance Criteria**
- Results update according to applied filters
- Each result displays first name, last name, and village
- Results are displayed in a clear list format

---

### US-SR-07: Handle no matching results
**As a user**  
I want to receive feedback when no residents match my search and filter criteria  
So that I understand the outcome of my request.

**Acceptance Criteria**
- A clear message is displayed when no results are found
- Message does not prevent further searches or filter changes

---

## Resident Management

### US-SR-08: Edit resident from search results
**As a user**  
I want to access a resident’s record directly from search results  
So that I can update their information.

**Acceptance Criteria**
- Each result includes an **Edit** button
- Clicking **Edit** opens the Edit Resident page for that resident

---

## Navigation & Usability

### US-SR-09: Return to home page
**As a user**  
I want to return to the home page from the search screen  
So that I can continue using the system.

**Acceptance Criteria**
- Home button navigates to the home page

---

## System Feedback

### US-SR-10: Display validation and system messages
**As a user**  
I want to see clear system messages during search and filtering  
So that I understand what actions are required or what went wrong.

**Acceptance Criteria**
- Validation and warning messages are visible and user-friendly
- Messages do not block further interaction
