"""
Scheme schemas.
"""
from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class SchemeOut(BaseModel):
    """Scheme output for list/search."""
    id: UUID
    name: str
    ministry: Optional[str] = None
    level: str
    state: Optional[str] = None
    category: List[str] = []
    description: str
    benefits: str
    application_mode: Optional[str] = None
    is_active: bool
    last_synced: datetime
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class SchemeDetail(SchemeOut):
    """Full scheme details."""
    eligibility_criteria: Dict[str, Any] = {}
    required_documents: List[str] = []
    application_url: Optional[str] = None
    source_url: Optional[str] = None


class SchemeCreate(BaseModel):
    """Create scheme (for ingestion)."""
    name: str
    ministry: Optional[str] = None
    level: str
    state: Optional[str] = None
    category: List[str] = []
    description: str
    benefits: str
    eligibility_criteria: Dict[str, Any] = {}
    required_documents: List[str] = []
    application_mode: Optional[str] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None


class EligibilityCheck(BaseModel):
    """Eligibility check result."""
    eligible: bool
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
