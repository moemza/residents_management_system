from .database import Base
from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

class Village(Base):
    __tablename__ = "villages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

class Resident(Base):
    __tablename__ = "residents"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    gender = Column(String, nullable=False)
    village = Column(String, nullable=False)
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
    name = Column(String)
    type = Column(String)
    level = Column(String)
    year = Column(String)
    resident_id = Column(Integer, ForeignKey("residents.id"))

    resident = relationship("Resident", back_populates="qualifications")

class Experience(Base):
    __tablename__ = "experiences"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String)
    position = Column(String)
    years = Column(String)
    resident_id = Column(Integer, ForeignKey("residents.id"))

    resident = relationship("Resident", back_populates="experiences")

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    resident_id = Column(Integer, ForeignKey("residents.id"))

    resident = relationship("Resident", back_populates="skills")