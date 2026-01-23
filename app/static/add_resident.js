flatpickr("#dob", { 
    dateFormat: "Y-m-d", 
    allowInput: true, 
    maxDate: "today" 
});

// Delete education row
function deleteEducationRow(btn) {
    const row = btn.closest('.education-row');
    const section = document.getElementById("education-section");
    const rows = section.querySelectorAll('.education-row');
    if (rows.length > 1) {
        row.remove();
    } else {
        // Remove the last row entirely if it's the only one
        row.remove();
    }
}

// Add education row
function addEducation() {
    const section = document.getElementById("education-section");
    const rows = section.querySelectorAll(".education-row");
    let lastRow = rows[rows.length - 1];

    // If there are no rows, create a new blank row
    if (rows.length === 0) {
        const newRow = document.createElement("div");
        newRow.className = "row g-2 mb-3 education-row";
        newRow.innerHTML = `
            <div class="col-md-3">
                <input name="education_institution[]" class="form-control" placeholder="Institution">
            </div>
            <div class="col-md-3">
                <select name="education_name[]" class="form-select" required>
                    <option value="">Name</option>
                    ${window.educationNamesHTML}
                </select>
            </div>
            <div class="col-md-2">
                <select name="education_type[]" class="form-select" required>
                    <option value="">Type</option>
                    ${window.educationTypesHTML}
                </select>
            </div>
            <div class="col-md-2">
                <select name="education_level[]" class="form-select" required>
                    <option value="">Level</option>
                    ${window.educationLevelsHTML}
                </select>
            </div>
            <div class="col-md-2 d-flex align-items-center">
                <input name="education_year[]" class="form-control" placeholder="Year">
                <button type="button" class="btn btn-danger btn-sm ms-2 delete-education-row" onclick="deleteEducationRow(this)">&#10006;</button>
            </div>
        `;
        section.appendChild(newRow);
        return;
    }

    // Otherwise, validate last row before adding
    let allFilled = true;
    lastRow.querySelectorAll("input, select").forEach(el => {
        if (!el.value || el.value.trim() === "") {
            allFilled = false;
        }
    });

    if (!allFilled) {
        alert("Please complete all fields in the current education row before adding another.");
        return;
    }

    // Clone and clear values
    const newRow = lastRow.cloneNode(true);
    newRow.querySelectorAll("input, select").forEach(el => el.value = "");
    section.appendChild(newRow);
}

// Add experience row
function addExperience() {
    const section = document.getElementById("experience-section");
    const rows = section.querySelectorAll(".experience-row");
    let lastRow = rows[rows.length - 1];

    // If there are no rows, create a new blank row
    if (rows.length === 0) {
        const newRow = document.createElement("div");
        newRow.className = "row g-2 mb-3 experience-row";
        newRow.innerHTML = `
            <div class="col-md-4">
                <input name="company[]" class="form-control" placeholder="Company">
            </div>
            <div class="col-md-4">
                <input name="position[]" class="form-control" placeholder="Position">
            </div>
            <div class="col-md-3">
                <input name="years[]" class="form-control" placeholder="Years">
            </div>
            <div class="col-md-1 d-flex align-items-center">
                <button type="button" class="btn btn-danger btn-sm delete-experience-row" onclick="deleteExperienceRow(this)">&#10006;</button>
            </div>
        `;
        section.appendChild(newRow);
        return;
    }

    // Otherwise, validate last row before adding
    let allFilled = true;
    lastRow.querySelectorAll("input").forEach(el => {
        if (!el.value || el.value.trim() === "") {
            allFilled = false;
        }
    });

    if (!allFilled) {
        alert("Please complete all fields in the current experience row before adding another.");
        return;
    }

    // Clone and clear values
    const newRow = lastRow.cloneNode(true);
    newRow.querySelectorAll("input").forEach(el => el.value = "");
    section.appendChild(newRow);
}

function deleteExperienceRow(btn) {
    const row = btn.closest('.experience-row');
    const section = document.getElementById("experience-section");
    const rows = section.querySelectorAll('.experience-row');
    // Remove the row, even if it's the last one
    row.remove();
}

// Add skill row
function addSkill() {
    const section = document.getElementById("skills-section");
    const rows = section.querySelectorAll(".skill-row");
    let lastRow = rows[rows.length - 1];

    // If there are no rows, create a new blank row
    if (rows.length === 0) {
        const newRow = document.createElement("div");
        newRow.className = "row g-2 mb-3 skill-row";
        newRow.innerHTML = `
            <div class="col-md-10">
                <input name="skills[]" class="form-control" placeholder="Skill">
            </div>
            <div class="col-md-2 d-flex align-items-center">
                <button type="button" class="btn btn-danger btn-sm ms-2 delete-skill-row" onclick="deleteSkillRow(this)">&#10006;</button>
            </div>
        `;
        section.appendChild(newRow);
        return;
    }

    // Validate last row before adding
    let allFilled = true;
    lastRow.querySelectorAll("input").forEach(el => {
        if (!el.value || el.value.trim() === "") {
            allFilled = false;
        }
    });

    if (!allFilled) {
        alert("Please complete the current skill before adding another.");
        return;
    }

    // Clone and clear values
    const newRow = lastRow.cloneNode(true);
    newRow.querySelectorAll("input").forEach(el => el.value = "");
    section.appendChild(newRow);
}

function deleteSkillRow(btn) {
    const row = btn.closest(".skill-row");
    row.remove();
    // No need to auto-add a blank row; user can click "+ Add Skill" to add one back
}