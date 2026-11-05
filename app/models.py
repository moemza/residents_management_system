from datetime import datetime, timezone

from .database import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class Resident(Base):
    __tablename__ = "residents"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False, index=True)
    last_name = Column(String, nullable=False, index=True)
    dob = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    village = Column(String, nullable=False, index=True)
    cellphone_no = Column(String, nullable=False)
    cellphone_no2 = Column(String)
    email = Column(String)

    qualifications = relationship("Qualification", back_populates="resident", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="resident", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="resident", cascade="all, delete-orphan")

class Qualification(Base):
    __tablename__ = "qualifications"

    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String)
    name = Column(String, index=True)
    type = Column(String)
    level = Column(String)
    year = Column(String)
    resident_id = Column(Integer, ForeignKey("residents.id"), index=True)

    resident = relationship("Resident", back_populates="qualifications")

class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String)
    position = Column(String)
    years = Column(String)
    resident_id = Column(Integer, ForeignKey("residents.id"), index=True)

    resident = relationship("Resident", back_populates="experiences")

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"), index=True)

    resident = relationship("Resident", back_populates="skills")


class AuditEvent(Base):
    """Non-PII record of a write operation.

    There is intentionally no foreign key to ``residents``: the audit trail must
    survive deletion of the resident it describes.
    """

    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
    action = Column(String, nullable=False, index=True)
    resident_id = Column(Integer, nullable=True, index=True)
    actor = Column(String, nullable=False)
    request_id = Column(String, nullable=True)
    detail = Column(String, nullable=True)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(20), nullable=False, default="admin")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    sessions = relationship(
        "AdminSession", back_populates="user", cascade="all, delete-orphan"
    )


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)

    user = relationship("AdminUser", back_populates="sessions")