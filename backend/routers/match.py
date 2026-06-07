"""
Scheme matching router.
"""
import logging
import time
from uuid import UUID
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.database import get_db_session
from backend.auth.jwt_handler import get_current_user
from backend.schemas.match import MatchRequest, MatchResponse, TranslateRequest, TranslateResponse
from backend.models.user import User, UserProfile
from backend.models.scheme import Scheme
from backend.cache.redis_client import RedisClient, compute_hash
from backend.services.rule_engine import RuleEngine
from backend.services.groq_service import GroqService
from backend.services.scoring import ScoringService
from backend.services.translation import TranslationService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/match", tags=["match"])

groq_service = GroqService()


@router.post("", response_model=MatchResponse)
async def match_schemes(
    request: MatchRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: UUID = Depends(get_current_user)
) -> dict:
    """
    Match schemes for a user based on profile.
    
    Args:
        request: Match request with user_id.
        session: Database session.
        current_user_id: Current user ID from JWT.
    
    Returns:
        Matched schemes with scores.
    """
    start_time = time.time()
    user_id = request.user_id
    
    # Only allow users to get their own matches
    if user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot get matches for other users"
        )
    
    # Get user profile
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalars().first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )
    
    # Compute profile hash
    profile_hash = compute_hash({
        "age": profile.age,
        "gender": profile.gender,
        "state": profile.state,
        "annual_income": profile.annual_income,
        "caste": profile.caste,
        "occupation": profile.occupation,
        "education": profile.education,
        "bpl_card": profile.bpl_card,
        "disability": profile.disability,
        "land_holding": profile.land_holding,
        "marital_status": profile.marital_status,
    })
    
    # Check cache
    cache_key = f"match:{profile_hash}"
    cached = await RedisClient.get_json(cache_key)
    if cached:
        logger.info(f"Match cache hit for user: {user_id}")
        return cached
    
    # Get all active schemes
    result = await session.execute(
        select(Scheme).where(Scheme.is_active == True)
    )
    all_schemes = result.scalars().all()
    
    logger.info(f"Total schemes in database: {len(all_schemes)}")
    
    # Rule engine filtering
    eligible_schemes = RuleEngine.filter_schemes(profile, all_schemes)
    logger.info(f"Schemes after rule engine: {len(eligible_schemes)}")
    
    # Evaluate custom rules with Groq
    groq_results: Dict[str, Any] = {}
    for scheme in eligible_schemes:
        custom_rules = scheme.eligibility_criteria.get("custom_rules", [])
        if custom_rules:
            result = await groq_service.evaluate_custom_rules(profile, scheme, profile_hash)
            groq_results[str(scheme.id)] = result
            
            # Filter out ineligible schemes
            if not result.get("eligible", True):
                eligible_schemes = [s for s in eligible_schemes if s.id != scheme.id]
    
    logger.info(f"Schemes after Groq evaluation: {len(eligible_schemes)}")
    
    # Score and rank
    match_results = ScoringService.score_and_rank(eligible_schemes, groq_results, profile)
    
    # Translate results if needed
    if profile.preferred_language and profile.preferred_language != "en":
        logger.info(f"Translating results to {profile.preferred_language}")
        for result in match_results:
            # Translate scheme name
            result.scheme_name = await TranslationService.translate(
                result.scheme_name,
                profile.preferred_language
            )
            # Translate benefits
            result.benefits = await TranslationService.translate(
                result.benefits,
                profile.preferred_language
            )
    
    # Build response
    evaluation_time = (time.time() - start_time) * 1000  # Convert to ms
    
    response = {
        "user_id": user_id,
        "total_matches": len(match_results),
        "matched_schemes": match_results,
        "evaluation_time_ms": evaluation_time
    }
    
    # Cache result (24 hours)
    await RedisClient.set_json(cache_key, response, 86400)
    
    logger.info(f"Match completed for user {user_id}: {len(match_results)} schemes, {evaluation_time:.2f}ms")
    
    return response


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(
    request: TranslateRequest,
    current_user_id: UUID = Depends(get_current_user)
) -> dict:
    """
    Translate text to target language.
    
    Args:
        request: Translation request.
        current_user_id: Current user ID from JWT.
    
    Returns:
        Translated text.
    """
    translated = await TranslationService.translate(
        request.text,
        request.target_language
    )
    
    return {
        "translated_text": translated,
        "target_language": request.target_language
    }
