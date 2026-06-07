"""
Authentication schemas.
"""
from pydantic import BaseModel, Field


class OTPRequest(BaseModel):
    """Request to send OTP."""
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number")


class OTPVerify(BaseModel):
    """Request to verify OTP."""
    phone: str = Field(..., min_length=10, max_length=15, description="Phone number")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class TokenResponse(BaseModel):
    """Response with JWT token."""
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool


class OTPResponse(BaseModel):
    """Response for OTP send request."""
    message: str
    expires_in: int
