import html
from datetime import date
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from .database import get_db, backup_database
from .models import Resident, Qualification, Experience, Skill
from .qualifications import get_all_qualifications
from .villages import get_all_villages

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────────

class QualificationIn(BaseModel):
    institution: str
    name: str
    type: str
    level: str
    year: str

class ExperienceIn(BaseModel):
    company: str
    position: str
    years: str

class SkillIn(BaseModel):
    name: str

class ResidentIn(BaseModel):
    first_name: str
    last_name: str
    dob: date
    gender: str
    village: str
    cellphone_no: str
    cellphone_no2: Optional[str] = None
    email: Optional[EmailStr] = None
    qualifications: List[QualificationIn] = Field(default_factory=list)
    experiences: List[ExperienceIn] = Field(default_factory=list)
    skills: List[SkillIn] = Field(default_factory=list)

    @field_validator("dob", mode="after")
    @classmethod
    def dob_not_in_future(cls, v):
        if v and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("first_name", "last_name", "gender", "village", "cellphone_no", mode="before")
    @classmethod
    def sanitize_str(cls, v):
        return html.escape(str(v).strip()) if v else v

    @field_validator("cellphone_no2", mode="before")
    @classmethod
    def sanitize_optional_str(cls, v):
        return html.escape(str(v).strip()) if v else None


def _resident_to_dict(r: Resident) -> dict:
    return {
        "id": r.id,
        "first_name": r.first_name,
        "last_name": r.last_name,
        "dob": str(r.dob),
        "gender": r.gender,
        "village": r.village,
        "cellphone_no": r.cellphone_no,
        "cellphone_no2": r.cellphone_no2,
        "email": r.email,
        "qualifications": [
            {"id": q.id, "institution": q.institution, "name": q.name,
             "type": q.type, "level": q.level, "year": q.year}
            for q in r.qualifications
        ],
        "experiences": [
            {"id": e.id, "company": e.company, "position": e.position, "years": e.years}
            for e in r.experiences
        ],
        "skills": [{"id": s.id, "name": s.name} for s in r.skills],
    }


# ── Reference data ─────────────────────────────────────────────────────────────

@router.get("/villages")
def list_villages():
    return get_all_villages()


@router.get("/qualifications")
def list_qualifications():
    return get_all_qualifications()


# ── Residents CRUD ─────────────────────────────────────────────────────────────

@router.get("/residents")
def list_residents(db: Session = Depends(get_db)):
    return [_resident_to_dict(r) for r in db.query(Resident).all()]


@router.get("/residents/{resident_id}")
def get_resident(resident_id: int, db: Session = Depends(get_db)):
    r = db.query(Resident).filter(Resident.id == resident_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resident not found")
    return _resident_to_dict(r)


@router.post("/residents", status_code=201)
def create_resident(payload: ResidentIn, db: Session = Depends(get_db)):
    resident = Resident(
        first_name=payload.first_name,
        last_name=payload.last_name,
        dob=payload.dob,
        gender=payload.gender,
        village=payload.village,
        cellphone_no=payload.cellphone_no,
        cellphone_no2=payload.cellphone_no2,
        email=payload.email,
        qualifications=[Qualification(**q.model_dump()) for q in payload.qualifications],
        experiences=[Experience(**e.model_dump()) for e in payload.experiences],
        skills=[Skill(**s.model_dump()) for s in payload.skills],
    )
    db.add(resident)
    db.commit()
    db.refresh(resident)
    backup_database()
    return _resident_to_dict(resident)


@router.put("/residents/{resident_id}")
def update_resident(resident_id: int, payload: ResidentIn, db: Session = Depends(get_db)):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    db.query(Qualification).filter(Qualification.resident_id == resident_id).delete()
    db.query(Experience).filter(Experience.resident_id == resident_id).delete()
    db.query(Skill).filter(Skill.resident_id == resident_id).delete()

    for key, value in payload.model_dump(exclude={"qualifications", "experiences", "skills"}).items():
        setattr(resident, key, value)

    for q in payload.qualifications:
        db.add(Qualification(**q.model_dump(), resident_id=resident_id))
    for e in payload.experiences:
        db.add(Experience(**e.model_dump(), resident_id=resident_id))
    for s in payload.skills:
        db.add(Skill(**s.model_dump(), resident_id=resident_id))

    db.commit()
    db.refresh(resident)
    backup_database()
    return _resident_to_dict(resident)


@router.delete("/residents/{resident_id}", status_code=204)
def delete_resident(resident_id: int, db: Session = Depends(get_db)):
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")
    db.delete(resident)
    db.commit()
    backup_database()


# ── Search ─────────────────────────────────────────────────────────────────────

@router.get("/search")
def search_residents(
    query: str = "",
    search_type: str = "name",
    db: Session = Depends(get_db),
):
    if not query.strip():
        return []

    safe_query = f"%{html.escape(query.strip())}%"

    if search_type == "name":
        results = db.query(Resident).filter(
            (Resident.first_name.ilike(safe_query)) | (Resident.last_name.ilike(safe_query))
        ).all()
    elif search_type == "village":
        results = db.query(Resident).filter(Resident.village.ilike(safe_query)).all()
    elif search_type == "qualification":
        results = db.query(Resident).join(Resident.qualifications).filter(
            Qualification.name.ilike(safe_query)
        ).all()
    elif search_type == "skill":
        results = db.query(Resident).join(Resident.skills).filter(
            Skill.name.ilike(safe_query)
        ).all()
    else:
        results = []

    return [_resident_to_dict(r) for r in results]
