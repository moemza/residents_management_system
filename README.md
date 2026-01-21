# Residents Management System

A web-based application for managing resident records, including personal details, qualifications, and village information.  
The backend is built with **FastAPI (Python)** and serves **HTML templates** for data entry and validation.

---

## Features

- Create and manage resident records  
- Maintain village and qualification reference data  
- Server-side validation using **Pydantic**  
- Dynamic form population from backend endpoints  
- Lightweight local JSON data storage  

---

## Project Structure

├── main.py # FastAPI application entry point
├── qualifications.py # Qualification data and logic
├── schemas.py # Pydantic models and validation
├── my_local_data.json # Local data storage for villages and qualifications
├── templates/
│ └── add_resident.html # HTML form for adding residents
├── Requirement.txt # Python dependencies
├── Dockerfile # Optional Docker configuration
├── README.md # Project documentation
└── .venv/ # Python virtual environment

---

## Requirements

- Python **3.11** or newer  
- `pip` package manager  

---

## Installation

### 1. Clone the Repository
Download or clone the repository to your local machine.

### 2. Create a Virtual Environment
Create a virtual environment named `.venv` using Python.

Activate the virtual environment before installing dependencies.

### 3. Install Dependencies
Install all required Python packages listed in `Requirement.txt`.

---

## Running the Application

- Start the FastAPI development server using **Uvicorn**
- Enable auto-reload for development
- Access the application locally at: [http://localhost:8000](http://localhost:8000)


---

## Application Usage

1. Open the resident form endpoint in a web browser  
2. Enter resident personal details  
3. Select villages and qualifications from dropdown lists  
4. Submit the form to store resident data  

> Dropdown values are automatically populated from backend endpoints.

---

## Configuration

### Villages and Qualifications
- Village data is stored in `my_local_data.json`
- Qualification structures are defined in `qualifications.py`
- Both can be modified to add or update options

### Validation
- Email fields are validated using **Pydantic**
- Required fields are enforced at the schema level
- Invalid submissions return clear validation errors

---

## Development Notes

- Uses **FastAPI template rendering**
- No external database is required
- Designed for easy future database integration

---

## License

This project is for **demonstration and educational purposes only**.

