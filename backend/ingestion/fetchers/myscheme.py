"""
MyScheme.gov.in fetcher using Playwright.
"""
import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from playwright.async_api import async_playwright, Page
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.models.scheme import Scheme
from backend.ingestion.normaliser import SchemeNormaliser


logger = logging.getLogger(__name__)


class MySchemeFetcher:
    """Fetcher for MyScheme portal using Playwright."""
    
    BASE_URL = "https://www.myscheme.gov.in"
    
    async def scrape(self) -> int:
        """
        Scrape and sync schemes from MyScheme.
        
        Returns:
            Number of schemes synced.
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                schemes = await self._scrape_schemes(page)
                synced = await self._save_schemes(schemes)
                return synced
            finally:
                await browser.close()
    
    async def _scrape_schemes(self, page: Page) -> List[Dict[str, Any]]:
        """
        Scrape scheme listings from MyScheme.
        
        Args:
            page: Playwright page object.
        
        Returns:
            List of scheme data.
        """
        schemes = []
        
        try:
            await page.goto(f"{self.BASE_URL}/schemes", wait_until="networkidle")
            
            # Wait for scheme items to load
            await page.wait_for_selector(".scheme-item", timeout=10000)
            
            # Extract scheme links
            scheme_links = await page.query_selector_all(".scheme-item a")
            
            for link in scheme_links:
                try:
                    href = await link.get_attribute("href")
                    if href:
                        # Rate limiting: 1 request per 2 seconds
                        await asyncio.sleep(2)
                        
                        # Get individual scheme details
                        scheme = await self._scrape_scheme_detail(page, href)
                        if scheme:
                            schemes.append(scheme)
                except Exception as e:
                    logger.warning(f"Error scraping scheme: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping MyScheme: {str(e)}")
        
        return schemes
    
    async def _scrape_scheme_detail(self, page: Page, url: str) -> Dict[str, Any]:
        """
        Scrape individual scheme details.
        
        Args:
            page: Playwright page object.
            url: Scheme URL.
        
        Returns:
            Scheme data.
        """
        try:
            await page.goto(url, wait_until="networkidle")
            
            scheme_data = {
                "name": await self._extract_text(page, "h1"),
                "description": await self._extract_text(page, ".description"),
                "benefits": await self._extract_text(page, ".benefits"),
                "eligibility": await self._extract_text(page, ".eligibility"),
                "required_documents": await self._extract_documents(page),
                "application_url": url,
                "source_url": url,
            }
            
            return scheme_data
        
        except Exception as e:
            logger.warning(f"Error scraping scheme details: {str(e)}")
            return None
    
    async def _extract_text(self, page: Page, selector: str) -> str:
        """Extract text from page element."""
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.text_content()
        except Exception:
            pass
        return ""
    
    async def _extract_documents(self, page: Page) -> List[str]:
        """Extract required documents list."""
        try:
            docs = []
            elements = await page.query_selector_all(".documents li")
            for elem in elements:
                doc = await elem.text_content()
                if doc:
                    docs.append(doc.strip())
            return docs
        except Exception:
            return []
    
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
                    normalised = SchemeNormaliser.normalise(scheme_data, "myscheme")
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
