"""
User profile schemas.
"""
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    """Create user profile."""
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, description="male, female, or other")
    state: Optional[str] = None
    district: Optional[str] = None
    annual_income: Optional[int] = Field(None, ge=0)
    caste: Optional[str] = Field(None, description="General, OBC, SC, ST, or NT")
    occupation: Optional[str] = None
    education: Optional[str] = None
    bpl_card: Optional[bool] = False
    disability: Optional[bool] = False
    disability_type: Optional[str] = None
    land_holding: Optional[float] = Field(None, ge=0)
    marital_status: Optional[str] = None
    owns_house: Optional[bool] = False
    jan_dhan_account: Optional[bool] = False
    preferred_language: Optional[str] = Field(None, description="ISO language code, e.g., 'ta', 'hi', 'en'")


class ProfileUpdate(ProfileCreate):
    """Update user profile."""
    pass


class ProfileOut(BaseModel):
    """User profile output schema."""
    id: UUID
    user_id: UUID
    age: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    annual_income: Optional[int] = None
    caste: Optional[str] = None
    occupation: Optional[str] = None
    education: Optional[str] = None
    bpl_card: Optional[bool] = None
    disability: Optional[bool] = None
    disability_type: Optional[str] = None
    land_holding: Optional[float] = None
    marital_status: Optional[str] = None
    owns_house: Optional[bool] = None
    jan_dhan_account: Optional[bool] = None
    preferred_language: Optional[str] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True
