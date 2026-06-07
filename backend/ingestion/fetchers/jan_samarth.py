"""
Jan Samarth API fetcher.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.scheme import Scheme
from backend.ingestion.normaliser import SchemeNormaliser


logger = logging.getLogger(__name__)


class JanSamarthFetcher:
    """Fetcher for Jan Samarth API."""
    
    BASE_URL = "https://jansamarth.nic.in/api"
    
    async def sync(self) -> int:
        """
        Fetch and sync schemes from Jan Samarth.
        
        Returns:
            Number of schemes synced.
        """
        try:
            schemes = await self._fetch_schemes()
            synced = await self._save_schemes(schemes)
            return synced
        except Exception as e:
            logger.error(f"Error syncing Jan Samarth: {str(e)}")
            return 0
    
    async def _fetch_schemes(self) -> List[Dict[str, Any]]:
        """
        Fetch schemes from Jan Samarth API.
        
        Returns:
            List of scheme data.
        """
        schemes = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch central schemes
                response = await client.get(
                    f"{self.BASE_URL}/schemes",
                    params={"level": "central"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    schemes.extend(data.get("schemes", []))
                
                # Fetch state schemes
                response = await client.get(
                    f"{self.BASE_URL}/schemes",
                    params={"level": "state"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    schemes.extend(data.get("schemes", []))
        
        except Exception as e:
            logger.error(f"Error fetching from Jan Samarth API: {str(e)}")
        
        return schemes
    
    async def _save_schemes(self, schemes: List[Dict[str, Any]]) -> int:
        """
        Save schemes to database.
        
        Args:
            schemes: List of scheme data.
        
        Returns:
            Number of schemes saved.
        """
        synced = 0
        
        async with get_db() as session:
            for scheme_data in schemes:
                try:
                    normalised = SchemeNormaliser.normalise(scheme_data, "jan_samarth")
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
