from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr
import json
from typing import List, Optional
from schemas import Village, ResidentCreate, Resident
import os
from contextlib import asynccontextmanager
from qualifications import get_all_qualifications

DATA_FILE = "my_local_data.json"
templates = Jinja2Templates(directory="templates")

def read_data():
    if not os.path.exists(DATA_FILE):
        return {"villages": [], "residents": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Hardcoded villages list
HARDCODED_VILLAGES = [
    {"id": 1, "name": "Garagopola"},
    {"id": 2, "name": "GaMohlophi"},
    {"id": 3, "name": "Makgemeng"},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # No longer pre-populate villages in the JSON file
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/villages/", response_model=List[Village])
def get_villages():
    """Retrieves the list of all villages."""
    return HARDCODED_VILLAGES

@app.get("/form", response_class=HTMLResponse)
def get_resident_form(request: Request):
    """Displays the form to add a new resident."""
    return templates.TemplateResponse("add_resident.html", {"request": request})

@app.post("/residents/form")
async def form_submit(
    request: Request,
    full_name: str = Form(...),
    national_id: str = Form(...),
    gender: str = Form(...),
    date_of_birth: str = Form(...),
    village_id: int = Form(...),
    stand_number: str = Form(...),
    contact_number_1: str = Form(...),
    contact_number_2: Optional[str] = Form(None),
    email: Optional[str] = Form(None),  # Change to str
    skills: Optional[str] = Form(None),
    qualification_type: str = Form(...),
    qualification_field: str = Form(...),
    qualification_level: str = Form(...),
    qualification_name: str = Form(...),
):
    # Convert empty email to None
    email_value = email if email and email.strip() else None

    data = read_data()
    new_resident_id = len(data["residents"]) + 1

    resident_data = ResidentCreate(
        full_name=full_name,
        national_id=national_id,
        gender=gender,
        date_of_birth=date_of_birth,
        village_id=village_id,
        stand_number=stand_number,
        contact_number_1=contact_number_1,
        contact_number_2=contact_number_2,
        email=email_value,  # Use cleaned value
        skills=skills,
        qualification_type=qualification_type,
        qualification_field=qualification_field,
        qualification_level=qualification_level,
        qualification_name=qualification_name,
    )

    # Use hardcoded villages for lookup
    village_info = next((v for v in HARDCODED_VILLAGES if v["id"] == village_id), None)

    new_resident = Resident(
        id=new_resident_id,
        **resident_data.model_dump(),
        village=village_info
    )

    data["residents"].append(new_resident.model_dump())
    write_data(data)
    
    return RedirectResponse(url="/form", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Redirects to the resident submission form."""
    return RedirectResponse(url="/form")

@app.get("/qualifications/")
def get_qualifications():
    return get_all_qualifications()