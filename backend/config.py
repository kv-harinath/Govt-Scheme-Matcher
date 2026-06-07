"""
Configuration module using Pydantic Settings.
Loads environment variables from .env file.
"""
import logging
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration from environment variables."""

    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # OTP Services
    msg91_api_key: Optional[str] = None
    fast2sms_api_key: Optional[str] = None
    
    # JWT
    jwt_secret: str
    jwt_expiry_hours: int = 72
    
    # Groq LLM
    groq_api_key: str
    groq_model: str = "llama3-70b-8192"
    
    # Data Sources
    data_gov_api_key: Optional[str] = None
    bhashini_api_key: Optional[str] = None
    
    # Translation Service
    indictrans_url: str = "http://localhost:8001/translate"
    
    # Backend Configuration
    backend_url: str = "http://localhost:8000"
    admin_email: str = "admin@example.com"
    environment: str = "development"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def configure_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


# Global settings instance
settings = get_settings()
logger = logging.getLogger(__name__)

# Configure logging on import
configure_logging(settings.log_level)
