"""
Scheme SQLAlchemy model.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, Text, Boolean, DateTime, Index, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB, TSVECTOR
import enum

from backend.models import Base


class LevelEnum(str, enum.Enum):
    """Scheme level enumeration."""
    central = "central"
    state = "state"


class ApplicationModeEnum(str, enum.Enum):
    """Application mode enumeration."""
    online = "online"
    offline = "offline"
    csc = "csc"


class Scheme(Base):
    """Government scheme model."""
    __tablename__ = "schemes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    ministry = Column(String(255), nullable=True)
    level = Column(String(20), nullable=False, default="central")  # central or state
    state = Column(String(50), nullable=True)  # Null for central schemes
    
    # Categorization
    category = Column(ARRAY(String), nullable=False, default=[])
    
    # Description
    description = Column(Text, nullable=False)
    benefits = Column(Text, nullable=False)
    
    # Eligibility criteria stored as JSONB
    eligibility_criteria = Column(JSONB, nullable=False, default={})
    
    # Required documents
    required_documents = Column(ARRAY(String), nullable=False, default=[])
    
    # Application details
    application_mode = Column(String(20), nullable=True)  # online, offline, csc
    application_url = Column(String(500), nullable=True)
    
    # Source tracking
    source_url = Column(String(500), nullable=True, unique=True, index=True)
    last_synced = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Active status
    is_active = Column(Boolean, nullable=False, default=False)
    
    # Full-text search vector (maintained via triggers in production)
    search_vector = Column(TSVECTOR, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_eligibility_criteria_gin', 'eligibility_criteria', postgresql_using='gin'),
        Index('idx_search_vector_gin', 'search_vector', postgresql_using='gin'),
        Index('idx_state', 'state'),
        Index('idx_level', 'level'),
        Index('idx_is_active', 'is_active'),
        Index('idx_category', 'category', postgresql_using='gin'),
    )
    
    def __repr__(self) -> str:
        return f"<Scheme(id={self.id}, name={self.name}, level={self.level})>"
