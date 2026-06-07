"""
User and UserProfile SQLAlchemy models.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
import enum

from backend.models import Base


class GenderEnum(str, enum.Enum):
    """Gender enumeration."""
    male = "male"
    female = "female"
    other = "other"


class CasteEnum(str, enum.Enum):
    """Caste enumeration."""
    general = "General"
    obc = "OBC"
    sc = "SC"
    st = "ST"
    nt = "NT"


class OccupationEnum(str, enum.Enum):
    """Occupation enumeration."""
    farmer = "farmer"
    student = "student"
    salaried = "salaried"
    self_employed = "self_employed"
    unemployed = "unemployed"
    daily_wage = "daily_wage"


class MaritalStatusEnum(str, enum.Enum):
    """Marital status enumeration."""
    single = "single"
    married = "married"
    widow = "widow"
    divorced = "divorced"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, phone={self.phone})>"


class UserProfile(Base):
    """User profile with eligibility criteria."""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Demographics
    age = Column(Integer, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    state = Column(String(50), nullable=True)
    district = Column(String(50), nullable=True)
    
    # Financial
    annual_income = Column(Integer, nullable=True)
    bpl_card = Column(Boolean, nullable=True, default=False)
    owns_house = Column(Boolean, nullable=True, default=False)
    land_holding = Column(Float, nullable=True)
    
    # Social
    caste = Column(Enum(CasteEnum), nullable=True)
    occupation = Column(Enum(OccupationEnum), nullable=True)
    education = Column(String(50), nullable=True)
    marital_status = Column(Enum(MaritalStatusEnum), nullable=True)
    
    # Health
    disability = Column(Boolean, nullable=True, default=False)
    disability_type = Column(String(100), nullable=True)
    
    # Banking
    jan_dhan_account = Column(Boolean, nullable=True, default=False)
    
    # Preferences
    preferred_language = Column(String(10), nullable=True, default="en")
    profile_hash = Column(String(32), nullable=True, index=True)  # MD5 hash for caching
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, state={self.state})>"
