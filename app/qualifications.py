# qualifications.py
# Central configuration for qualification options
# Easy to modify and extend

QUALIFICATION_TYPES = [
    "Certificate",
    "Diploma",
    "Degree",
    "Postgraduate",
    "Professional Qualification",
    "Vocational Training",
    "Short Course",
    "Online Course",
    "Apprenticeship",
    "Workshop",
    "Bootcamp",
    "Informal Training"
]

QUALIFICATION_FIELDS = [
    "Agriculture",
    "Arts & Humanities",
    "Business & Management",
    "Community Development",
    "Construction",
    "Economics",
    "Education",
    "Engineering",
    "Environmental Studies",
    "Finance & Accounting",
    "Health Sciences",
    "Hospitality & Tourism",
    "Information Technology",
    "Languages",
    "Law",
    "Manufacturing",
    "Mathematics",
    "Media & Communication",
    "Medicine",
    "Nursing",
    "Pharmacy",
    "Public Health",
    "Science",
    "Security & Safety",
    "Social Sciences",
    "Sports & Physical Education",
    "Technology",
    "Transport & Logistics"
]

QUALIFICATION_LEVELS = [
    "NQF Level 1 (Grade 9 / ABET Level 4)",
    "NQF Level 2 (Grade 10 / National Certificate)",
    "NQF Level 3 (Grade 11 / National Certificate)",
    "NQF Level 4 (Grade 12 / National Senior Certificate)",
    "NQF Level 5 (Higher Certificate)",
    "NQF Level 6 (Advanced Certificate / Diploma)",
    "NQF Level 7 (Bachelor’s Degree / Advanced Diploma)",
    "NQF Level 8 (Honours Degree / Postgraduate Diploma)",
    "NQF Level 9 (Master’s Degree)",
    "NQF Level 10 (Doctoral Degree)",

    # Professional & Non-Formal
    "Occupational Qualification (QCTO)",
    "Professional Qualification (Professional Body)",
    "Skills Programme",
    "Short Course",
    "Non-Formal / Informal Training"
]

QUALIFICATION_NAMES = {
    "Science": [
        "Biology",
        "Chemistry",
        "Physics",
        "Environmental Science"
    ],
    "Technology": [
        "Digital Technology",
        "Applied Technology"
    ],
    "Engineering": [
        "Civil Engineering",
        "Mechanical Engineering",
        "Electrical Engineering",
        "Mechatronics",
        "Chemical Engineering"
    ],
    "Mathematics": [
        "Pure Mathematics",
        "Applied Mathematics",
        "Statistics"
    ],
    "Information Technology": [
        "Computer Literacy",
        "Computer Science",
        "Information Systems",
        "Software Engineering",
        "Web Development",
        "Data Science",
        "Cybersecurity",
        "Networking",
        "Database Administration"
    ],
    "Business & Management": [
        "Business Administration",
        "Accounting",
        "Finance",
        "Marketing",
        "Human Resource Management",
        "Entrepreneurship",
        "Project Management"
    ],
    "Finance & Accounting": [
        "Financial Accounting",
        "Management Accounting",
        "Auditing",
        "Taxation"
    ],
    "Economics": [
        "Microeconomics",
        "Macroeconomics",
        "Development Economics"
    ],
    "Health Sciences": [
        "Clinical Medicine",
        "Health Records Management",
        "Laboratory Technology"
    ],
    "Medicine": [
        "Medicine and Surgery",
        "Clinical Practice"
    ],
    "Nursing": [
        "General Nursing",
        "Midwifery",
        "Community Nursing"
    ],
    "Pharmacy": [
        "Pharmacy Practice",
        "Pharmaceutical Sciences"
    ],
    "Public Health": [
        "Public Health Practice",
        "Epidemiology",
        "Health Promotion"
    ],
    "Education": [
        "Early Childhood Education",
        "Primary Education",
        "Secondary Education",
        "Special Needs Education",
        "Educational Leadership"
    ],
    "Law": [
        "Law",
        "Legal Studies",
        "Paralegal Studies"
    ],
    "Social Sciences": [
        "Sociology",
        "Psychology",
        "Social Work"
    ],
    "Arts & Humanities": [
        "History",
        "Philosophy",
        "Fine Arts"
    ],
    "Languages": [
        "English",
        "Xitsonga",
        "Afrikaans",
        "Language Translation"
    ],
    "Agriculture": [
        "Agricultural Management",
        "Crop Production",
        "Animal Production"
    ],
    "Environmental Studies": [
        "Environmental Management",
        "Climate Studies"
    ],
    "Construction": [
        "Building Construction",
        "Quantity Surveying"
    ],
    "Manufacturing": [
        "Manufacturing Technology",
        "Production Management"
    ],
    "Hospitality & Tourism": [
        "Hospitality Management",
        "Tourism Management"
    ],
    "Transport & Logistics": [
        "Logistics Management",
        "Supply Chain Management"
    ],
    "Media & Communication": [
        "Journalism",
        "Public Relations",
        "Media Studies"
    ],
    "Sports & Physical Education": [
        "Sports Science",
        "Physical Education"
    ],
    "Security & Safety": [
        "Security Management",
        "Occupational Health and Safety"
    ],
    "Community Development": [
        "Community Development Practice",
        "Local Governance"
    ],

    # Informal Qualifications (explicit and complete)
    "Informal Training": [
        "Leadership Skills",
        "Communication Skills",
        "Digital Skills",
        "Financial Literacy",
        "Life Skills",
        "First Aid",
        "Community Health Training",
        "Entrepreneurial Skills",
        "Conflict Resolution",
        "Basic Computer Skills",
        "Youth Development Training",
        "Volunteer Training"
    ]
}

def get_all_qualifications():
    """
    Returns a full structured dictionary of all qualifications.
    Useful for APIs or form generation.
    """
    return {
        "types": QUALIFICATION_TYPES,
        "fields": QUALIFICATION_FIELDS,
        "levels": QUALIFICATION_LEVELS,
        "names": QUALIFICATION_NAMES
    }
