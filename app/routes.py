from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import Resident, Qualification, Experience, Skill
from .schemas import ResidentCreate
from fastapi.templating import Jinja2Templates
from .qualifications import get_all_qualifications
from .villages import get_all_villages
from starlette.responses import RedirectResponse
from datetime import datetime

router = APIRouter()
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@router.get("/search_resident", response_class=HTMLResponse)
async def search_resident_form(request: Request):
    return templates.TemplateResponse("search_resident.html", {"request": request, "results": None, "message": None})

@router.get("/search-resident", response_class=HTMLResponse)
async def search_resident(request: Request, query: str = "", db: Session = Depends(get_db)):
    if not query:
        return templates.TemplateResponse("search_resident.html", {
            "request": request,
            "results": None,
            "message": "Please enter a search term."
        })
    
    # Basic search logic - you can expand this
    residents = db.query(Resident).filter(
        Resident.first_name.ilike(f"%{query}%") | 
        Resident.last_name.ilike(f"%{query}%") |
        Resident.cellphone_no.ilike(f"%{query}%")
    ).all()
    
    return templates.TemplateResponse("search_resident.html", {
        "request": request,
        "results": residents,
        "message": None
    })

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

@router.get("/edit-resident/{resident_id}", response_class=HTMLResponse)
async def edit_resident_form(request: Request, resident_id: int, db: Session = Depends(get_db)):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        return RedirectResponse(url="/", status_code=303)
    
    villages = get_all_villages()
    qualifications = get_all_qualifications()
    
    return templates.TemplateResponse(
        "edit_resident.html",
        {
            "request": request,
            "resident": resident,
            "villages": villages,
            "qualifications": qualifications
        }
    )

@router.post("/edit-resident/{resident_id}")
async def edit_resident(
    request: Request,
    resident_id: int,
    db: Session = Depends(get_db)
):
    form = await request.form()
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        return RedirectResponse(url="/", status_code=303)
    
    # Update resident fields
    resident.first_name = form.get("first_name")
    resident.last_name = form.get("last_name")
    resident.gender = form.get("gender")
    resident.village = form.get("village")
    dob_str = form.get("dob")
    if dob_str:
        resident.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    resident.cellphone_no = form.get("cellphone_no")
    resident.cellphone_no2 = form.get("cellphone_no2")
    resident.email = form.get("email")
    
    # Note: For simplicity, we're not updating qualifications/experiences/skills here
    # You would need more complex logic to handle those relationships
    
    db.commit()
    db.refresh(resident)
    
    return RedirectResponse(url="/", status_code=303)


@router.post("/add_resident")
async def add_resident(
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()
    # Extract personal details
    first_name = form.get("first_name")
    last_name = form.get("last_name")
    gender = form.get("gender")
    village = form.get("village")
    dob_str = form.get("dob")
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
    cellphone_no = form.get("cellphone_no")
    cellphone_no2 = form.get("cellphone_no2")
    email = form.get("email")

    # Extract education
    institutions = form.getlist("education_institution[]")
    names = form.getlist("education_name[]")
    types = form.getlist("education_type[]")
    levels = form.getlist("education_level[]")
    years = form.getlist("education_year[]")
    qualifications = [  # <-- renamed from 'education'
        Qualification(
            institution=institutions[i],
            name=names[i],
            type=types[i],          # <-- change from 'qualification_type'
            level=levels[i],        # <-- change from 'qualification_level'
            year=years[i]
        )
        for i in range(len(institutions))
    ]

    # Extract experience
    companies = form.getlist("company[]")
    positions = form.getlist("position[]")
    years_exp = form.getlist("years[]")
    experiences = [  # <-- renamed from 'experience'
        Experience(
            company=companies[i],
            position=positions[i],
            years=years_exp[i]
        )
        for i in range(len(companies))
    ]

    # Extract skills
    skills_list = form.getlist("skills[]")
    skills = [Skill(name=s) for s in skills_list]

    # Create resident
    resident = Resident(
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        gender=gender,
        village=village,
        cellphone_no=cellphone_no,
        cellphone_no2=cellphone_no2,
        email=email,
        qualifications=qualifications,
        experiences=experiences,
        skills=skills
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)

    return RedirectResponse(url="/", status_code=303)