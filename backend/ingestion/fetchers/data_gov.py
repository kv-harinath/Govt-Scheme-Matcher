"""
data.gov.in API fetcher for schemes.
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.database import get_db
from backend.models.scheme import Scheme
from backend.ingestion.normaliser import SchemeNormaliser


logger = logging.getLogger(__name__)


class DataGovFetcher:
    """Fetcher for data.gov.in scheme API."""
    
    BASE_URL = "https://data.gov.in/api/datastore/sql"
    RESOURCE_IDS = [
        "9ef6b8cd-361f-4776-9ac6-213b1d5bfc20",  # Central Sector Schemes
        "5a2e9eb7-3aac-4a4e-8b8a-6e6c5e5e5e5e",  # State-Level Schemes
    ]
    
    async def sync(self) -> int:
        """
        Fetch and sync schemes from data.gov.in.
        
        Returns:
            Number of schemes synced.
        """
        total_synced = 0
        
        for resource_id in self.RESOURCE_IDS:
            try:
                count = await self._sync_resource(resource_id)
                total_synced += count
                logger.info(f"Synced {count} schemes from resource {resource_id}")
            except Exception as e:
                logger.error(f"Error syncing resource {resource_id}: {str(e)}")
        
        return total_synced
    
    async def _sync_resource(self, resource_id: str) -> int:
        """
        Sync a specific resource from data.gov.in.
        
        Args:
            resource_id: Resource ID to fetch.
        
        Returns:
            Number of schemes synced.
        """
        synced = 0
        limit = 100
        offset = 0
        
        async with get_db() as session:
            while True:
                records = await self._fetch_records(resource_id, limit, offset)
                
                if not records:
                    break
                
                for record in records:
                    try:
                        normalised = SchemeNormaliser.normalise(record, "data.gov.in")
                        await self._upsert_scheme(session, normalised)
                        synced += 1
                    except Exception as e:
                        logger.warning(f"Error normalising record: {str(e)}")
                
                offset += limit
        
        return synced
    
    async def _fetch_records(
        self,
        resource_id: str,
        limit: int,
        offset: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch records from data.gov.in API.
        
        Args:
            resource_id: Resource ID.
            limit: Number of records.
            offset: Record offset.
        
        Returns:
            List of records.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "resource_id": resource_id,
                        "limit": limit,
                        "offset": offset,
                        "api_key": settings.data_gov_api_key,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("records", [])
                else:
                    logger.error(f"API returned status {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching from API: {str(e)}")
            return []
    
    async def _upsert_scheme(
        self,
        session: AsyncSession,
        scheme_data: Dict[str, Any]
    ) -> None:
        """
        Upsert scheme into database.
        
        Args:
            session: Database session.
            scheme_data: Normalised scheme data.
        """
        source_url = scheme_data.get("source_url")
        
        if not source_url:
            logger.warning("Scheme missing source_url, skipping")
            return
        
        # Check if scheme exists by source_url
        result = await session.execute(
            select(Scheme).where(Scheme.source_url == source_url)
        )
        existing = result.scalars().first()
        
        if existing:
            # Update existing
            for key, value in scheme_data.items():
                setattr(existing, key, value)
            existing.last_synced = datetime.utcnow()
        else:
            # Create new
            scheme = Scheme(**scheme_data)
            session.add(scheme)
        
        await session.commit()
