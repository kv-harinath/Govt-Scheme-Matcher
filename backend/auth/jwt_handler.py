"""
JWT token creation and verification.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials

from backend.config import settings


security = HTTPBearer()


def create_access_token(
    user_id: UUID,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        user_id: User UUID.
        expires_delta: Optional expiry delta. Defaults to JWT_EXPIRY_HOURS.
    
    Returns:
        Encoded JWT token.
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=settings.jwt_expiry_hours)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm="HS256"
    )
    return encoded_jwt


def decode_token(token: str) -> UUID:
    """
    Decode and verify JWT token.
    
    Args:
        token: JWT token.
    
    Returns:
        User UUID from token.
    
    Raises:
        HTTPException: If token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return UUID(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> UUID:
    """
    Dependency to get current user from JWT.
    
    Args:
        credentials: HTTP Bearer credentials.
    
    Returns:
        User UUID.
    
    Raises:
        HTTPException: If token is invalid.
    """
    return decode_token(credentials.credentials)
