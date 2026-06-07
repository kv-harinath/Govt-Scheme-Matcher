"""
Match request/response schemas.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    """Request to match schemes for a user."""
    user_id: UUID


class MatchResult(BaseModel):
    """Result for a single matched scheme."""
    scheme_id: UUID
    scheme_name: str
    category: List[str]
    level: str
    state: Optional[str] = None
    score: float = Field(ge=0.0, le=1.0, description="Match score 0-1")
    match_reason: str
    eligibility_reason: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, description="Groq LLM confidence for custom rules")
    application_mode: Optional[str] = None
    application_url: Optional[str] = None
    required_documents: List[str] = []
    benefits: str


class MatchResponse(BaseModel):
    """Response with matched schemes."""
    user_id: UUID
    total_matches: int
    matched_schemes: List[MatchResult]
    evaluation_time_ms: float
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class TranslateRequest(BaseModel):
    """Request to translate text."""
    text: str = Field(..., min_length=1, max_length=5000)
    target_language: str = Field(..., min_length=2, max_length=5)


class TranslateResponse(BaseModel):
    """Translated text response."""
    translated_text: str
    target_language: str
