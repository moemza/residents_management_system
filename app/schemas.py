from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class EducationBase(BaseModel):
    institution: str
    qualification_name: str
    qualification_type: str
    qualification_level: str
    year: str

class ExperienceBase(BaseModel):
    company: str
    position: str
    years: str

class SkillBase(BaseModel):
    skill: str

class ResidentBase(BaseModel):
    first_name: str
    last_name: str
    gender: str
    village: str
    dob: date
    cellphone_no: str
    cellphone_no2: Optional[str] = None
    email: Optional[str] = None

class ResidentCreate(ResidentBase):
    qualifications: List[EducationBase]
    experience: List[ExperienceBase]
    skills: List[SkillBase]

class Resident(ResidentBase):
    id: int
    qualifications: List[EducationBase]
    experience: List[ExperienceBase]
    skills: List[SkillBase]

    class Config:
        orm_mode = True