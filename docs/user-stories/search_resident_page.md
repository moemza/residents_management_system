# Search Resident Page – User Stories

## Epic: Search and Filter Residents

**As a system user,**  
I want to search for residents using different criteria,  
so that I can quickly locate specific resident records.

---

## Search Type Selection

### US-SR-01: Select a search type
**As a user**  
I want to choose how I search (by name, village, qualification, or skill)  
so that I can find residents using the most relevant criteria.

**Acceptance Criteria**
- A dropdown lets the user select: Name or Surname, Village, Qualification, Skill
- Changing the search type resets the query input and clears results
- The selected type is reflected in the URL query string (`?type=name`)

---

## Search Input

### US-SR-02: Search by name
**As a user**  
I want to type a name or surname into a text input  
so that I can find residents by their name.

**Acceptance Criteria**
- Free-text input is shown when search type is `name` or `skill`
- Partial matches are returned (case-insensitive)

---

### US-SR-03: Search by village
**As a user**  
I want to select a village from a dropdown  
so that I can view all residents from a specific location.

**Acceptance Criteria**
- A village dropdown (populated from `GET /api/villages`) is shown when type is `village`

---

### US-SR-04: Search by qualification field
**As a user**  
I want to select a qualification field from a dropdown  
so that I can find residents with qualifications in a specific area.

**Acceptance Criteria**
- A qualification field dropdown (populated from `GET /api/qualifications`) is shown when type is `qualification`

---

## Results

### US-SR-05: View search results
**As a user**  
I want to see a list of matching residents  
so that I can identify the correct person quickly.

**Acceptance Criteria**
- Each result shows: first name, last name, village
- Each result has a **View** button linking to `/view-resident/{id}`
- Each result has an **Edit** button linking to `/edit-resident/{id}`
- Result count is shown above the list

---

### US-SR-06: Handle no results
**As a user**  
I want to see a clear message when no residents match my search  
so that I understand the outcome.

**Acceptance Criteria**
- "No residents found matching your search criteria." is shown when results are empty
- The message does not prevent further searches

---

### US-SR-07: Validate empty search
**As a user**  
I want to be told if I submit a search without entering a term  
so that I don't get confusing empty results.

**Acceptance Criteria**
- Submitting with an empty query shows "Please enter a search term."
- No API call is made for empty queries

---

## Feedback

### US-SR-08: Handle search errors
**As a user**  
I want to see a message if the search fails  
so that I know something went wrong.

**Acceptance Criteria**
- If the API call fails, "Search failed. Please try again." is shown
- The error does not crash the page
