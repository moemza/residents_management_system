"""Pydantic request and response schemas for the Residents API.

Input validation is deliberately strict at the boundary. Output schemas are
explicit so the OpenAPI contract is accurate and new database columns are not
leaked to clients by accident.
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

MAX_NAME_LENGTH = 100
MAX_PHONE_LENGTH = 30
MAX_EMAIL_LENGTH = 254
MAX_TEXT_LENGTH = 200
MAX_YEAR_LENGTH = 20
MAX_CHILD_ROWS = 50


def _clean_required(value) -> str:
    """Trim a required text value and reject blank or HTML-markup content."""
    if value is None:
        raise ValueError("Field cannot be empty")
    text = str(value).strip()
    if not text:
        raise ValueError("Field cannot be empty")
    if "<" in text or ">" in text:
        raise ValueError("HTML markup is not allowed")
    return text


def _clean_optional(value) -> Optional[str]:
    """Trim an optional text value; empty values become None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "<" in text or ">" in text:
        raise ValueError("HTML markup is not allowed")
    return text


class QualificationIn(BaseModel):
    institution: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    name: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    type: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    level: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    year: str = Field(min_length=1, max_length=MAX_YEAR_LENGTH)

    @field_validator("institution", "name", "type", "level", "year", mode="before")
    @classmethod
    def clean(cls, value):
        return _clean_required(value)


class ExperienceIn(BaseModel):
    company: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    position: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    years: str = Field(min_length=1, max_length=MAX_YEAR_LENGTH)

    @field_validator("company", "position", "years", mode="before")
    @classmethod
    def clean(cls, value):
        return _clean_required(value)


class SkillIn(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)

    @field_validator("name", mode="before")
    @classmethod
    def clean(cls, value):
        return _clean_required(value)


class ResidentIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    last_name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    dob: date
    gender: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    village: str = Field(min_length=1, max_length=MAX_NAME_LENGTH)
    cellphone_no: str = Field(min_length=1, max_length=MAX_PHONE_LENGTH)
    cellphone_no2: Optional[str] = Field(default=None, max_length=MAX_PHONE_LENGTH)
    email: Optional[EmailStr] = Field(default=None, max_length=MAX_EMAIL_LENGTH)
    qualifications: List[QualificationIn] = Field(
        default_factory=list, max_length=MAX_CHILD_ROWS
    )
    experiences: List[ExperienceIn] = Field(
        default_factory=list, max_length=MAX_CHILD_ROWS
    )
    skills: List[SkillIn] = Field(default_factory=list, max_length=MAX_CHILD_ROWS)

    @field_validator("dob", mode="after")
    @classmethod
    def reject_future_dob(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return value

    @field_validator(
        "first_name", "last_name", "gender", "village", "cellphone_no", mode="before"
    )
    @classmethod
    def clean_required(cls, value):
        return _clean_required(value)

    @field_validator("cellphone_no2", "email", mode="before")
    @classmethod
    def clean_optional(cls, value):
        return _clean_optional(value)


class QualificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    institution: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None
    level: Optional[str] = None
    year: Optional[str] = None


class ExperienceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company: Optional[str] = None
    position: Optional[str] = None
    years: Optional[str] = None


class SkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: Optional[str] = None


class ResidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    dob: date
    gender: str
    village: str
    cellphone_no: str
    cellphone_no2: Optional[str] = None
    email: Optional[str] = None
    qualifications: List[QualificationOut] = Field(default_factory=list)
    experiences: List[ExperienceOut] = Field(default_factory=list)
    skills: List[SkillOut] = Field(default_factory=list)


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    action: str
    resident_id: Optional[int] = None
    actor: str
    request_id: Optional[str] = None
    detail: Optional[str] = None


class AuthStatusOut(BaseModel):
    auth_required: bool
    authenticated: bool = False
    csrf_token: Optional[str] = None


class AdminLoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=1024)


class AdminLoginOut(BaseModel):
    authenticated: bool
    csrf_token: str


class HealthOut(BaseModel):
    status: str
    database: str


class ErrorOut(BaseModel):
    detail: str
