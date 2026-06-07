"""
Authentication router.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db_session
from backend.schemas.auth import OTPRequest, OTPVerify, TokenResponse, OTPResponse
from backend.services.otp_service import OTPService
from backend.auth.jwt_handler import create_access_token
from backend.models.user import User
from sqlalchemy import select
from datetime import datetime


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(
    request: OTPRequest,
    session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Send OTP to phone number.
    
    Args:
        request: OTP request with phone number.
        session: Database session.
    
    Returns:
        Message and expiry time.
    """
    phone = request.phone.strip()
    
    # Validate phone format
    if not phone.isdigit() or len(phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number"
        )
    
    # Send OTP
    success = await OTPService.send_otp(phone)
    
    if not success:
        logger.error(f"Failed to send OTP to {phone}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again."
        )
    
    return {
        "message": "OTP sent successfully",
        "expires_in": 600
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    request: OTPVerify,
    session: AsyncSession = Depends(get_db_session)
) -> dict:
    """
    Verify OTP and return JWT token.
    
    Args:
        request: OTP verification request.
        session: Database session.
    
    Returns:
        JWT token and user status.
    """
    phone = request.phone.strip()
    otp = request.otp.strip()
    
    # Verify OTP
    is_valid = await OTPService.verify_otp(phone, otp)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP"
        )
    
    # Check if user exists
    result = await session.execute(
        select(User).where(User.phone == phone)
    )
    user = result.scalars().first()
    
    is_new_user = user is None
    
    if user is None:
        # Create new user
        user = User(phone=phone, last_login=datetime.utcnow())
        session.add(user)
        await session.flush()
        logger.info(f"New user created: {phone}")
    else:
        # Update last login
        user.last_login = datetime.utcnow()
    
    await session.commit()
    
    # Generate JWT token
    access_token = create_access_token(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_new_user": is_new_user
    }
