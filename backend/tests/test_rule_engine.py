"""Tests for rule engine."""

import pytest
from uuid import uuid4
from datetime import datetime

from backend.services.rule_engine import RuleEngine
from backend.models.user import UserProfile, GenderEnum, CasteEnum
from backend.models.scheme import Scheme


@pytest.fixture
def sample_profile():
    """Create sample user profile for testing."""
    return UserProfile(
        id=uuid4(),
        user_id=uuid4(),
        age=35,
        gender=GenderEnum.male,
        state="Tamil Nadu",
        annual_income=300000,
        caste=CasteEnum.general,
        occupation="salaried",
        education="Bachelor's",
        bpl_card=False,
        disability=False,
        land_holding=None,
        marital_status="single",
        jan_dhan_account=True
    )


@pytest.fixture
def sample_scheme():
    """Create sample scheme for testing."""
    return Scheme(
        id=uuid4(),
        name="Test Scheme",
        level="central",
        category=["General"],
        description="Test",
        benefits="Benefits",
        eligibility_criteria={
            "age_min": 18,
            "age_max": 60,
            "income_max_annual": 500000,
            "gender": ["male", "female"],
            "caste": ["General", "OBC"]
        },
        source_url="https://example.com",
        last_synced=datetime.utcnow(),
        is_active=True
    )


def test_age_check_eligible(sample_profile, sample_scheme):
    """Test age eligibility check."""
    assert RuleEngine._check_age(sample_profile.age, sample_scheme.eligibility_criteria)


def test_age_check_too_young(sample_profile, sample_scheme):
    """Test age check when user is too young."""
    profile = sample_profile
    profile.age = 15
    assert not RuleEngine._check_age(profile.age, sample_scheme.eligibility_criteria)


def test_age_check_too_old(sample_profile, sample_scheme):
    """Test age check when user is too old."""
    profile = sample_profile
    profile.age = 65
    assert not RuleEngine._check_age(profile.age, sample_scheme.eligibility_criteria)


def test_gender_check_eligible(sample_profile, sample_scheme):
    """Test gender eligibility check."""
    assert RuleEngine._check_gender(sample_profile.gender, sample_scheme.eligibility_criteria)


def test_gender_check_ineligible():
    """Test gender check when ineligible."""
    criteria = {"gender": ["female"]}
    assert not RuleEngine._check_gender(GenderEnum.male, criteria)


def test_income_check_eligible(sample_profile, sample_scheme):
    """Test income eligibility check."""
    assert RuleEngine._check_income(sample_profile.annual_income, sample_scheme.eligibility_criteria)


def test_income_check_ineligible(sample_profile, sample_scheme):
    """Test income check when ineligible."""
    profile = sample_profile
    profile.annual_income = 600000
    assert not RuleEngine._check_income(profile.annual_income, sample_scheme.eligibility_criteria)


def test_bpl_check_not_required():
    """Test BPL check when not required."""
    criteria = {}
    assert RuleEngine._check_bpl(False, criteria)


def test_bpl_check_required_but_missing():
    """Test BPL check when required but user doesn't have."""
    criteria = {"bpl_required": True}
    assert not RuleEngine._check_bpl(False, criteria)


def test_bpl_check_required_and_present():
    """Test BPL check when required and user has."""
    criteria = {"bpl_required": True}
    assert RuleEngine._check_bpl(True, criteria)


def test_is_eligible_all_pass(sample_profile, sample_scheme):
    """Test eligibility when all criteria pass."""
    result = RuleEngine._is_eligible(sample_profile, sample_scheme)
    assert result


def test_is_eligible_with_custom_rules():
    """Test eligibility with custom rules."""
    scheme = Scheme(
        id=uuid4(),
        name="Test",
        level="central",
        category=["General"],
        description="Test",
        benefits="Benefits",
        eligibility_criteria={
            "custom_rules": ["Must have Jan Dhan account"]
        },
        source_url="https://example.com",
        last_synced=datetime.utcnow(),
        is_active=True
    )
    
    profile = UserProfile(
        id=uuid4(),
        user_id=uuid4(),
        age=30,
        jan_dhan_account=True
    )
    
    # Should pass basic checks and leave custom rules for Groq
    result = RuleEngine._is_eligible(profile, scheme)
    assert result
