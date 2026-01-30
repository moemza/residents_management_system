from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from datetime import datetime
from .database import backup_database, get_db
from .models import Resident, Qualification, Experience, Skill
from .qualifications import get_all_qualifications
from .villages import get_all_villages
from fastapi.templating import Jinja2Templates

router = APIRouter()
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

def process_resident_form_data(form, resident_id=None):
    from .models import Qualification, Experience, Skill
    from datetime import datetime

    # Personal details
    first_name = form.get("first_name")
    last_name = form.get("last_name")
    gender = form.get("gender")
    village = form.get("village")
    dob_str = form.get("dob")
    dob = datetime.strptime(dob_str, "%Y-%m-%d").date() if dob_str else None
    cellphone_no = form.get("cellphone_no")
    cellphone_no2 = form.get("cellphone_no2")
    email = form.get("email")

    # Education
    institutions = form.getlist("education_institution[]")
    names = form.getlist("education_name[]")
    types = form.getlist("education_type[]")
    levels = form.getlist("education_level[]")
    years = form.getlist("education_year[]")
    qualifications = [
        Qualification(
            institution=institutions[i],
            name=names[i],
            type=types[i],
            level=levels[i],
            year=years[i],
            resident_id=resident_id
        )
        for i in range(len(institutions)) if institutions[i].strip()
    ]

    # Experience
    companies = form.getlist("company[]")
    positions = form.getlist("position[]")
    years_exp = form.getlist("years[]")
    experiences = [
        Experience(
            company=companies[i],
            position=positions[i],
            years=years_exp[i],
            resident_id=resident_id
        )
        for i in range(len(companies)) if companies[i].strip()
    ]

    # Skills
    skills_list = form.getlist("skills[]")
    skills = [
        Skill(
            name=s,
            resident_id=resident_id
        )
        for s in skills_list if s.strip()
    ]

    resident_data = {
        "first_name": first_name,
        "last_name": last_name,
        "dob": dob,
        "gender": gender,
        "village": village,
        "cellphone_no": cellphone_no,
        "cellphone_no2": cellphone_no2,
        "email": email,
    }
    return resident_data, qualifications, experiences, skills

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

    # Remove old related records
    db.query(Qualification).filter(Qualification.resident_id == resident_id).delete()
    db.query(Experience).filter(Experience.resident_id == resident_id).delete()
    db.query(Skill).filter(Skill.resident_id == resident_id).delete()

    # Process new data
    resident_data, qualifications, experiences, skills = process_resident_form_data(form, resident_id)

    # Update resident fields
    for key, value in resident_data.items():
        setattr(resident, key, value)

    # Add new related records
    for q in qualifications:
        db.add(q)
    for e in experiences:
        db.add(e)
    for s in skills:
        db.add(s)

    db.commit()
    db.refresh(resident)

    backup_database()

    return RedirectResponse(url="/", status_code=303)

@router.post("/add_resident")
async def add_resident(
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()
    resident_data, qualifications, experiences, skills = process_resident_form_data(form)

    resident = Resident(
        **resident_data,
        qualifications=qualifications,
        experiences=experiences,
        skills=skills
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)

    backup_database()

    return RedirectResponse(url="/", status_code=303)

@router.get("/view-resident/{resident_id}", response_class=HTMLResponse)
async def view_resident(request: Request, resident_id: int, db: Session = Depends(get_db)):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse(
        "view_resident.html",
        {
            "request": request,
            "resident": resident
        }
    )