"""Tests for matching endpoint."""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime

from backend.services.scoring import ScoringService
from backend.models.scheme import Scheme
from backend.models.user import UserProfile, GenderEnum


@pytest.fixture
def sample_schemes():
    """Create sample schemes for testing."""
    return [
        Scheme(
            id=uuid4(),
            name="Scheme 1",
            level="central",
            category=["Agriculture"],
            description="Farmer scheme",
            benefits="₹50,000 subsidy",
            eligibility_criteria={"occupation": ["farmer"]},
            source_url="https://example.com/1",
            last_synced=datetime.utcnow(),
            is_active=True,
            application_mode="online"
        ),
        Scheme(
            id=uuid4(),
            name="Scheme 2",
            level="central",
            category=["General"],
            description="General scheme",
            benefits="Benefits",
            eligibility_criteria={},
            source_url="https://example.com/2",
            last_synced=datetime.utcnow(),
            is_active=True,
            application_mode="offline"
        ),
    ]


@pytest.fixture
def sample_profile():
    """Create sample user profile."""
    return UserProfile(
        id=uuid4(),
        user_id=uuid4(),
        age=40,
        gender=GenderEnum.male,
        state="Tamil Nadu",
        annual_income=300000,
        occupation="farmer",
        education="10th",
        bpl_card=False,
        disability=False,
        jan_dhan_account=True
    )


def test_score_and_rank(sample_schemes, sample_profile):
    """Test scheme scoring and ranking."""
    groq_results = {}
    results = ScoringService.score_and_rank(sample_schemes, groq_results, sample_profile)
    
    assert len(results) <= ScoringService.MAX_RESULTS
    # Should be sorted by score (descending)
    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score


def test_score_with_groq_results(sample_schemes, sample_profile):
    """Test scoring with Groq evaluation results."""
    groq_results = {
        str(sample_schemes[0].id): {
            "eligible": True,
            "confidence": 0.9,
            "reason": "Eligible"
        }
    }
    
    results = ScoringService.score_and_rank(sample_schemes, groq_results, sample_profile)
    
    assert len(results) > 0
    # First scheme should have higher score due to groq confidence
    assert results[0].confidence == 0.9


def test_score_bounds(sample_schemes, sample_profile):
    """Test that scores are within valid bounds."""
    groq_results = {}
    results = ScoringService.score_and_rank(sample_schemes, groq_results, sample_profile)
    
    for result in results:
        assert 0.0 <= result.score <= 1.1  # Allow small overage for bonuses
