"""
Schemes router for browsing and searching schemes.
"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from sqlalchemy.sql import text

from backend.db.database import get_db_session
from backend.auth.jwt_handler import get_current_user
from backend.schemas.scheme import SchemeOut, SchemeDetail
from backend.models.scheme import Scheme


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.get("", response_model=List[SchemeOut])
async def list_schemes(
    category: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    mode: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user_id: UUID = Depends(get_current_user)
) -> List[SchemeOut]:
    """
    List schemes with optional filtering.
    
    Args:
        category: Filter by category.
        state: Filter by state.
        level: Filter by level (central/state).
        mode: Filter by application mode.
        page: Page number (1-indexed).
        limit: Results per page.
        session: Database session.
        current_user_id: Current user ID from JWT.
    
    Returns:
        List of schemes.
    """
    query = select(Scheme).where(Scheme.is_active == True)
    
    if category:
        query = query.where(Scheme.category.any(category))
    
    if state:
        query = query.where(or_(Scheme.state == state, Scheme.level == "central"))
    
    if level:
        query = query.where(Scheme.level == level)
    
    if mode:
        query = query.where(Scheme.application_mode == mode)
    
    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await session.execute(query)
    schemes = result.scalars().all()
    
    return [SchemeOut.model_validate(s) for s in schemes]


@router.get("/{scheme_id}", response_model=SchemeDetail)
async def get_scheme(
    scheme_id: UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user_id: UUID = Depends(get_current_user)
) -> SchemeDetail:
    """
    Get scheme details.
    
    Args:
        scheme_id: Scheme ID.
        session: Database session.
        current_user_id: Current user ID from JWT.
    
    Returns:
        Scheme details.
    """
    result = await session.execute(
        select(Scheme).where(Scheme.id == scheme_id)
    )
    scheme = result.scalars().first()
    
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheme not found"
        )
    
    return SchemeDetail.model_validate(scheme)


@router.get("/search/text", response_model=List[SchemeOut])
async def search_schemes(
    q: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    current_user_id: UUID = Depends(get_current_user)
) -> List[SchemeOut]:
    """
    Search schemes by text.
    
    Args:
        q: Search query.
        page: Page number.
        limit: Results per page.
        session: Database session.
        current_user_id: Current user ID from JWT.
    
    Returns:
        List of matching schemes.
    """
    # Simple text search on name and description
    search_term = f"%{q}%"
    
    query = select(Scheme).where(
        and_(
            Scheme.is_active == True,
            or_(
                Scheme.name.ilike(search_term),
                Scheme.description.ilike(search_term),
                Scheme.benefits.ilike(search_term)
            )
        )
    )
    
    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await session.execute(query)
    schemes = result.scalars().all()
    
    logger.info(f"Search query '{q}' returned {len(schemes)} results")
    
    return [SchemeOut.model_validate(s) for s in schemes]
