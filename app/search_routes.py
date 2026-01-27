from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from .database import get_db
from .models import Resident, Qualification, Skill
from .villages import get_all_villages
from .qualifications import QUALIFICATION_FIELDS
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Template mapping for different search types
template_map = {
    "name": "search_by_name.html",
    "village": "search_by_village.html",
    "qualification": "search_by_qualification.html",
    "skill": "search_by_skills.html"
}

@router.get("/search_resident", response_class=HTMLResponse)
def search_resident_form(request: Request, search_type: str = "name"):
    villages = get_all_villages()  # For resident search dropdown
    template_name = template_map.get(search_type, "search_by_name.html")
    
    # Pass qualification fields when search_type is "qualification"
    context = {
        "request": request, 
        "search_type": search_type, 
        "villages": villages
    }
    if search_type == "qualification":
        context["qualification_fields"] = QUALIFICATION_FIELDS
    
    return templates.TemplateResponse(template_name, context)

@router.get("/search-resident", response_class=HTMLResponse)
async def search_resident(
    request: Request, 
    query: str = "", 
    search_type: str = "name",
    db: Session = Depends(get_db)
):
    villages = get_all_villages()
    template_name = template_map.get(search_type, "search_by_name.html")
    
    if not query:
        context = {
            "request": request,
            "results": None,
            "message": "Please enter a search term.",
            "villages": villages,
            "selected_village": ""
        }
        if search_type == "qualification":
            context["qualification_fields"] = QUALIFICATION_FIELDS
        return templates.TemplateResponse(template_name, context)
    
    if search_type == "name":
        residents = db.query(Resident).filter(
            (Resident.first_name.ilike(f"%{query}%")) | 
            (Resident.last_name.ilike(f"%{query}%"))
        ).all()
    elif search_type == "village":
        residents = db.query(Resident).filter(
            Resident.village.ilike(f"%{query}%")
        ).all()
    elif search_type == "qualification":
        residents = db.query(Resident).join(Resident.qualifications).filter(
            Qualification.name.ilike(f"%{query}%")
        ).all()
    elif search_type == "skill":
        residents = db.query(Resident).join(Resident.skills).filter(
            Skill.name.ilike(f"%{query}%")
        ).all()
    else:
        residents = []

    context = {
        "request": request,
        "results": residents,
        "message": None,
        "villages": villages,
        "selected_village": ""
    }
    if search_type == "qualification":
        context["qualification_fields"] = QUALIFICATION_FIELDS
    
    return templates.TemplateResponse(template_name, context)