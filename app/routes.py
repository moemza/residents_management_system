from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import Resident, Education, Experience, Skill
from .schemas import ResidentCreate
from fastapi.templating import Jinja2Templates
from .qualifications import get_all_qualifications
from .villages import get_all_villages
from starlette.responses import RedirectResponse

router = APIRouter()
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@router.get("/add_resident", response_class=HTMLResponse)
async def add_resident_form(request: Request):
    qualifications = get_all_qualifications()
    villages = get_all_villages()
    return templates.TemplateResponse(
        "add_resident.html",
        {
            "request": request,
            "qualifications": qualifications,
            "villages": villages
        }
    )

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@router.post("/add_resident")
async def add_resident(
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()
    # Extract personal details
    name = form.get("name")
    surname = form.get("surname")
    gender = form.get("gender")
    village = form.get("village")
    date_of_birth = form.get("date_of_birth")
    cellphone_no = form.get("cellphone_no")
    cellphone_no2 = form.get("cellphone_no2")
    email = form.get("email")

    # Extract education
    institutions = form.getlist("education_institution[]")
    names = form.getlist("education_name[]")
    types = form.getlist("education_type[]")
    levels = form.getlist("education_level[]")
    years = form.getlist("education_year[]")
    education = [
        Education(
            institution=institutions[i],
            qualification_name=names[i],
            qualification_type=types[i],
            qualification_level=levels[i],
            year=years[i]
        )
        for i in range(len(institutions))
    ]

    # Extract experience
    companies = form.getlist("company[]")
    positions = form.getlist("position[]")
    years_exp = form.getlist("years[]")
    experience = [
        Experience(
            company=companies[i],
            position=positions[i],
            years=years_exp[i]
        )
        for i in range(len(companies))
    ]

    # Extract skills
    skills_list = form.getlist("skills[]")
    skills = [Skill(skill=s) for s in skills_list]

    # Create resident
    resident = Resident(
        name=name,
        surname=surname,
        gender=gender,
        village=village,
        date_of_birth=date_of_birth,
        cellphone_no=cellphone_no,
        cellphone_no2=cellphone_no2,
        email=email,
        education=education,
        experience=experience,
        skills=skills
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)

    return RedirectResponse(url="/", status_code=303)