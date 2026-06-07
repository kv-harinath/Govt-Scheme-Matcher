"""
State portal scrapers for Tamil Nadu, Maharashtra, UP, Karnataka, West Bengal.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.scheme import Scheme
from backend.ingestion.normaliser import SchemeNormaliser


logger = logging.getLogger(__name__)


class StatePortalsFetcher:
    """Fetcher for state portal schemes."""
    
    STATES = ["tamil_nadu", "maharashtra", "uttar_pradesh", "karnataka", "west_bengal"]
    
    async def scrape_all(self) -> int:
        """
        Scrape all state portals.
        
        Returns:
            Total number of schemes synced.
        """
        total_synced = 0
        
        for state in self.STATES:
            try:
                count = await self._scrape_state(state)
                total_synced += count
                logger.info(f"Synced {count} schemes from {state}")
            except Exception as e:
                logger.error(f"Error scraping {state}: {str(e)}")
        
        return total_synced
    
    async def _scrape_state(self, state: str) -> int:
        """
        Scrape schemes from a specific state.
        
        Args:
            state: State identifier.
        
        Returns:
            Number of schemes synced.
        """
        # State-specific scraping logic would go here
        # For now, return 0 as placeholder
        # In production, implement using Playwright or BeautifulSoup
        
        if state == "tamil_nadu":
            schemes = await self._scrape_tamil_nadu()
        elif state == "maharashtra":
            schemes = await self._scrape_maharashtra()
        elif state == "uttar_pradesh":
            schemes = await self._scrape_uttar_pradesh()
        elif state == "karnataka":
            schemes = await self._scrape_karnataka()
        elif state == "west_bengal":
            schemes = await self._scrape_west_bengal()
        else:
            return 0
        
        # Save schemes
        synced = await self._save_schemes(schemes, state)
        return synced
    
    async def _scrape_tamil_nadu(self) -> List[Dict[str, Any]]:
        """Scrape Tamil Nadu state schemes."""
        # Implement TN-specific scraping
        return []
    
    async def _scrape_maharashtra(self) -> List[Dict[str, Any]]:
        """Scrape Maharashtra state schemes."""
        # Implement Maharashtra-specific scraping
        return []
    
    async def _scrape_uttar_pradesh(self) -> List[Dict[str, Any]]:
        """Scrape Uttar Pradesh state schemes."""
        # Implement UP-specific scraping
        return []
    
    async def _scrape_karnataka(self) -> List[Dict[str, Any]]:
        """Scrape Karnataka state schemes."""
        # Implement Karnataka-specific scraping
        return []
    
    async def _scrape_west_bengal(self) -> List[Dict[str, Any]]:
        """Scrape West Bengal state schemes."""
        # Implement West Bengal-specific scraping
        return []
    
    async def _save_schemes(
        self,
        schemes: List[Dict[str, Any]],
        source: str
    ) -> int:
        """
        Save schemes to database.
        
        Args:
            schemes: List of scheme data.
            source: Source identifier.
        
        Returns:
            Number of schemes saved.
        """
        synced = 0
        
        async with get_db() as session:
            for scheme_data in schemes:
                try:
                    normalised = SchemeNormaliser.normalise(scheme_data, source)
                    await self._upsert_scheme(session, normalised)
                    synced += 1
                except Exception as e:
                    logger.warning(f"Error saving scheme: {str(e)}")
        
        return synced
    
    async def _upsert_scheme(
        self,
        session: AsyncSession,
        scheme_data: Dict[str, Any]
    ) -> None:
        """Upsert scheme into database."""
        source_url = scheme_data.get("source_url")
        
        if not source_url:
            return
        
        result = await session.execute(
            select(Scheme).where(Scheme.source_url == source_url)
        )
        existing = result.scalars().first()
        
        if existing:
            for key, value in scheme_data.items():
                setattr(existing, key, value)
            existing.last_synced = datetime.utcnow()
        else:
            scheme = Scheme(**scheme_data)
            session.add(scheme)
        
        await session.commit()
