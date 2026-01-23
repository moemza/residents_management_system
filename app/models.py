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
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    village = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    cellphone_no = Column(String, nullable=False)
    cellphone_no2 = Column(String, nullable=True)
    email = Column(String, nullable=True)
    # Relationships
    education = relationship("Education", back_populates="resident", cascade="all, delete-orphan")
    experience = relationship("Experience", back_populates="resident", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="resident", cascade="all, delete-orphan")

class Education(Base):
    __tablename__ = "education"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"))
    institution = Column(String, nullable=False)
    qualification_name = Column(String, nullable=False)
    qualification_type = Column(String, nullable=False)
    qualification_level = Column(String, nullable=False)
    year = Column(String, nullable=False)
    resident = relationship("Resident", back_populates="education")

class Experience(Base):
    __tablename__ = "experience"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"))
    company = Column(String, nullable=False)
    position = Column(String, nullable=False)
    years = Column(String, nullable=False)
    resident = relationship("Resident", back_populates="experience")

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("residents.id"))
    skill = Column(String, nullable=False)
    resident = relationship("Resident", back_populates="skills")