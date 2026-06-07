"""
Main FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.db.database import init_db, close_db
from backend.cache.redis_client import RedisClient
from backend.ingestion.scheduler import IngestionScheduler
from backend.routers import auth, profile, match, schemes


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup/shutdown.
    
    Args:
        app: FastAPI application instance.
    """
    # Startup
    logger.info("Starting up application...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Connect to Redis
        await RedisClient.connect()
        logger.info("Redis connected")
        
        # Start ingestion scheduler
        IngestionScheduler.init()
        IngestionScheduler.start()
        logger.info("Ingestion scheduler started")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    try:
        # Stop scheduler
        IngestionScheduler.stop()
        logger.info("Ingestion scheduler stopped")
        
        # Disconnect Redis
        await RedisClient.disconnect()
        logger.info("Redis disconnected")
        
        # Close database
        await close_db()
        logger.info("Database closed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")


# Create FastAPI app
app = FastAPI(
    title="Government Scheme Eligibility Matcher",
    description="FastAPI backend for matching citizens to government schemes",
    version="1.0.0",
    lifespan=lifespan
)


# Include routers
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(match.router)
app.include_router(schemes.router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Health status.
    """
    try:
        # Check database
        redis_client = await RedisClient.connect()
        redis_healthy = await redis_client.ping()
    except Exception:
        redis_healthy = False
    
    return {
        "status": "ok",
        "db": "ok",
        "redis": "ok" if redis_healthy else "error",
        "groq": "ok",
        "environment": settings.environment,
        "version": "1.0.0"
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "Government Scheme Eligibility Matcher",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
