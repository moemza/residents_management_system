from pydantic import BaseModel, EmailStr
from typing import Optional

class Village(BaseModel):
    id: int
    name: str

class ResidentCreate(BaseModel):
    full_name: str
    national_id: str
    gender: str
    date_of_birth: str
    village_id: int
    stand_number: str
    contact_number_1: str
    contact_number_2: Optional[str] = None
    email: Optional[EmailStr] = None
    skills: Optional[str] = None
    qualification_type: str
    qualification_field: str
    qualification_level: str
    qualification_name: str

class Resident(ResidentCreate):
    id: int
    village: Village