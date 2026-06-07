"""
User profile router.
"""
import hashlib
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db_session
from backend.auth.jwt_handler import get_current_user
from backend.schemas.profile import ProfileCreate, ProfileOut
from backend.models.user import User, UserProfile
from backend.cache.redis_client import RedisClient, compute_hash


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=ProfileOut)
async def create_or_update_profile(
    profile_data: ProfileCreate,
    session: AsyncSession = Depends(get_db_session),
    user_id: UUID = Depends(get_current_user)
) -> ProfileOut:
    """
    Create or update user profile.
    
    Args:
        profile_data: Profile data to create/update.
        session: Database session.
        user_id: Current user ID from JWT.
    
    Returns:
        Updated profile.
    """
    # Get user
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get or create profile
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalars().first()
    
    if profile is None:
        profile = UserProfile(user_id=user_id)
    
    # Update profile fields
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    
    # Compute profile hash for caching
    profile_dict = {
        "age": profile.age,
        "gender": profile.gender,
        "state": profile.state,
        "district": profile.district,
        "annual_income": profile.annual_income,
        "caste": profile.caste,
        "occupation": profile.occupation,
        "education": profile.education,
        "bpl_card": profile.bpl_card,
        "disability": profile.disability,
        "marital_status": profile.marital_status,
        "land_holding": profile.land_holding,
    }
    profile.profile_hash = compute_hash(profile_dict)
    
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    
    # Invalidate match cache for this user
    cache_key = f"match:{profile.profile_hash}"
    await RedisClient.delete(cache_key)
    
    logger.info(f"Profile updated for user: {user_id}")
    return ProfileOut.model_validate(profile)


@router.get("/{user_id}", response_model=ProfileOut)
async def get_profile(
    user_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: UUID = Depends(get_current_user)
) -> ProfileOut:
    """
    Get user profile.
    
    Args:
        user_id: User ID to fetch.
        session: Database session.
        current_user_id: Current user ID from JWT.
    
    Returns:
        User profile.
    """
    # Only allow users to view their own profile
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other user's profile"
        )
    
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalars().first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return ProfileOut.model_validate(profile)
