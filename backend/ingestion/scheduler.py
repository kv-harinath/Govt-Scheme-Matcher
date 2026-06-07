"""
APScheduler job definitions for data ingestion.
"""
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.ingestion.fetchers.data_gov import DataGovFetcher
from backend.ingestion.fetchers.myscheme import MySchemeFetcher
from backend.ingestion.fetchers.jan_samarth import JanSamarthFetcher
from backend.ingestion.fetchers.state_portals import StatePortalsFetcher


logger = logging.getLogger(__name__)


class IngestionScheduler:
    """Scheduler for periodic scheme data ingestion."""
    
    _scheduler: AsyncIOScheduler = None
    
    @classmethod
    def init(cls) -> AsyncIOScheduler:
        """
        Initialize the scheduler with all jobs.
        
        Returns:
            Configured AsyncIOScheduler instance.
        """
        if cls._scheduler is not None:
            return cls._scheduler
        
        cls._scheduler = AsyncIOScheduler()
        
        # Monday 02:00 AM - data.gov.in
        cls._scheduler.add_job(
            IngestionScheduler._sync_data_gov,
            "cron",
            day_of_week="mon",
            hour=2,
            minute=0,
            id="sync_data_gov",
            name="Sync data.gov.in schemes"
        )
        
        # Monday 03:00 AM - MyScheme
        cls._scheduler.add_job(
            IngestionScheduler._sync_myscheme,
            "cron",
            day_of_week="mon",
            hour=3,
            minute=0,
            id="sync_myscheme",
            name="Sync MyScheme schemes"
        )
        
        # Monday 04:00 AM - Jan Samarth
        cls._scheduler.add_job(
            IngestionScheduler._sync_jan_samarth,
            "cron",
            day_of_week="mon",
            hour=4,
            minute=0,
            id="sync_jan_samarth",
            name="Sync Jan Samarth schemes"
        )
        
        # Tuesday 02:00 AM - State Portals
        cls._scheduler.add_job(
            IngestionScheduler._sync_state_portals,
            "cron",
            day_of_week="tue",
            hour=2,
            minute=0,
            id="sync_state_portals",
            name="Sync state portal schemes"
        )
        
        return cls._scheduler
    
    @classmethod
    def start(cls) -> None:
        """Start the scheduler."""
        if cls._scheduler is None:
            cls.init()
        
        if not cls._scheduler.running:
            cls._scheduler.start()
            logger.info("Ingestion scheduler started")
    
    @classmethod
    def stop(cls) -> None:
        """Stop the scheduler."""
        if cls._scheduler and cls._scheduler.running:
            cls._scheduler.shutdown()
            logger.info("Ingestion scheduler stopped")
    
    @staticmethod
    async def _sync_data_gov() -> None:
        """Sync schemes from data.gov.in."""
        logger.info("Starting data.gov.in synchronization")
        start_time = datetime.utcnow()
        
        try:
            fetcher = DataGovFetcher()
            count = await fetcher.sync()
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"data.gov.in sync completed: {count} schemes in {duration:.2f}s")
        except Exception as e:
            logger.error(f"data.gov.in sync failed: {str(e)}")
            # Send admin alert email
            IngestionScheduler._send_admin_alert(
                "data.gov.in sync failed",
                f"Error: {str(e)}"
            )
    
    @staticmethod
    async def _sync_myscheme() -> None:
        """Sync schemes from MyScheme."""
        logger.info("Starting MyScheme synchronization")
        start_time = datetime.utcnow()
        
        try:
            fetcher = MySchemeFetcher()
            count = await fetcher.scrape()
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"MyScheme sync completed: {count} schemes in {duration:.2f}s")
        except Exception as e:
            logger.error(f"MyScheme sync failed: {str(e)}")
            IngestionScheduler._send_admin_alert(
                "MyScheme sync failed",
                f"Error: {str(e)}"
            )
    
    @staticmethod
    async def _sync_jan_samarth() -> None:
        """Sync schemes from Jan Samarth."""
        logger.info("Starting Jan Samarth synchronization")
        start_time = datetime.utcnow()
        
        try:
            fetcher = JanSamarthFetcher()
            count = await fetcher.sync()
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Jan Samarth sync completed: {count} schemes in {duration:.2f}s")
        except Exception as e:
            logger.error(f"Jan Samarth sync failed: {str(e)}")
            IngestionScheduler._send_admin_alert(
                "Jan Samarth sync failed",
                f"Error: {str(e)}"
            )
    
    @staticmethod
    async def _sync_state_portals() -> None:
        """Sync schemes from state portals."""
        logger.info("Starting state portal synchronization")
        start_time = datetime.utcnow()
        
        try:
            fetcher = StatePortalsFetcher()
            count = await fetcher.scrape_all()
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"State portals sync completed: {count} schemes in {duration:.2f}s")
        except Exception as e:
            logger.error(f"State portals sync failed: {str(e)}")
            IngestionScheduler._send_admin_alert(
                "State portals sync failed",
                f"Error: {str(e)}"
            )
    
    @staticmethod
    def _send_admin_alert(subject: str, message: str) -> None:
        """
        Send admin alert email on job failure.
        
        Args:
            subject: Email subject.
            message: Email message.
        """
        # TODO: Implement email sending via SMTP
        logger.warning(f"Admin alert: {subject} - {message}")
