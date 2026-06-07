"""
SQLAlchemy models for the application.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()

from backend.models.user import User, UserProfile
from backend.models.scheme import Scheme

__all__ = ["User", "UserProfile", "Scheme", "Base"]
