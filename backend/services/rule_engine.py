"""
Rule engine for eligibility matching.
"""
import logging
from typing import List, Optional

from backend.models.scheme import Scheme
from backend.models.user import UserProfile


logger = logging.getLogger(__name__)


class RuleEngine:
    """Eligibility rule matching engine."""
    
    @staticmethod
    def filter_schemes(profile: UserProfile, schemes: List[Scheme]) -> List[Scheme]:
        """
        Filter schemes based on user profile and eligibility criteria.
        
        Args:
            profile: User profile with eligibility information.
            schemes: List of schemes to filter.
        
        Returns:
            List of eligible schemes.
        """
        eligible_schemes = []
        
        for scheme in schemes:
            if RuleEngine._is_eligible(profile, scheme):
                eligible_schemes.append(scheme)
        
        return eligible_schemes
    
    @staticmethod
    def _is_eligible(profile: UserProfile, scheme: Scheme) -> bool:
        """
        Check if user profile matches scheme eligibility criteria.
        
        Args:
            profile: User profile.
            scheme: Scheme to check.
        
        Returns:
            True if user is eligible.
        """
        criteria = scheme.eligibility_criteria or {}
        
        # Check age
        if not RuleEngine._check_age(profile.age, criteria):
            return False
        
        # Check gender
        if not RuleEngine._check_gender(profile.gender, criteria):
            return False
        
        # Check income
        if not RuleEngine._check_income(profile.annual_income, criteria):
            return False
        
        # Check caste
        if not RuleEngine._check_caste(profile.caste, criteria):
            return False
        
        # Check state of residence
        if not RuleEngine._check_state(profile.state, criteria):
            return False
        
        # Check BPL requirement
        if not RuleEngine._check_bpl(profile.bpl_card, criteria):
            return False
        
        # Check occupation
        if not RuleEngine._check_occupation(profile.occupation, criteria):
            return False
        
        # Check disability
        if not RuleEngine._check_disability(profile.disability, criteria):
            return False
        
        # Check land holding
        if not RuleEngine._check_land_holding(profile.land_holding, criteria):
            return False
        
        # Check marital status
        if not RuleEngine._check_marital_status(profile.marital_status, criteria):
            return False
        
        # Check education
        if not RuleEngine._check_education(profile.education, criteria):
            return False
        
        return True
    
    @staticmethod
    def _check_age(age: Optional[int], criteria: dict) -> bool:
        """Check age eligibility."""
        if age is None or "age_min" not in criteria and "age_max" not in criteria:
            return True
        
        age_min = criteria.get("age_min")
        age_max = criteria.get("age_max")
        
        if age_min and age < age_min:
            return False
        if age_max and age > age_max:
            return False
        
        return True
    
    @staticmethod
    def _check_gender(gender: Optional[str], criteria: dict) -> bool:
        """Check gender eligibility."""
        if gender is None or "gender" not in criteria:
            return True
        
        allowed_genders = criteria.get("gender", [])
        if not allowed_genders:
            return True
        
        return gender.lower() in [g.lower() for g in allowed_genders]
    
    @staticmethod
    def _check_income(income: Optional[int], criteria: dict) -> bool:
        """Check annual income eligibility."""
        if income is None or "income_max_annual" not in criteria:
            return True
        
        income_max = criteria.get("income_max_annual")
        if income_max and income > income_max:
            return False
        
        return True
    
    @staticmethod
    def _check_caste(caste: Optional[str], criteria: dict) -> bool:
        """Check caste eligibility."""
        if caste is None or "caste" not in criteria:
            return True
        
        allowed_castes = criteria.get("caste", [])
        if not allowed_castes:
            return True
        
        return caste in allowed_castes
    
    @staticmethod
    def _check_state(state: Optional[str], criteria: dict) -> bool:
        """Check state of residence eligibility."""
        if state is None or "state_of_residence" not in criteria:
            return True
        
        allowed_states = criteria.get("state_of_residence", [])
        if not allowed_states:
            return True
        
        return state in allowed_states
    
    @staticmethod
    def _check_bpl(bpl_card: Optional[bool], criteria: dict) -> bool:
        """Check BPL requirement."""
        if bpl_card is None or "bpl_required" not in criteria:
            return True
        
        bpl_required = criteria.get("bpl_required", False)
        if bpl_required and not bpl_card:
            return False
        
        return True
    
    @staticmethod
    def _check_occupation(occupation: Optional[str], criteria: dict) -> bool:
        """Check occupation eligibility."""
        if occupation is None or "occupation" not in criteria:
            return True
        
        allowed_occupations = criteria.get("occupation", [])
        if not allowed_occupations:
            return True
        
        return occupation in allowed_occupations
    
    @staticmethod
    def _check_disability(disability: Optional[bool], criteria: dict) -> bool:
        """Check disability eligibility."""
        if disability is None or "disability" not in criteria:
            return True
        
        disability_required = criteria.get("disability")
        if disability_required is False and disability is True:
            return False
        
        return True
    
    @staticmethod
    def _check_land_holding(land_holding: Optional[float], criteria: dict) -> bool:
        """Check land holding eligibility."""
        if land_holding is None or "land_holding_max_acres" not in criteria:
            return True
        
        max_acres = criteria.get("land_holding_max_acres")
        if max_acres and land_holding > max_acres:
            return False
        
        return True
    
    @staticmethod
    def _check_marital_status(marital_status: Optional[str], criteria: dict) -> bool:
        """Check marital status eligibility."""
        if marital_status is None or "marital_status" not in criteria:
            return True
        
        allowed_statuses = criteria.get("marital_status", [])
        if not allowed_statuses:
            return True
        
        return marital_status in allowed_statuses
    
    @staticmethod
    def _check_education(education: Optional[str], criteria: dict) -> bool:
        """Check education eligibility."""
        if education is None or "education_max" not in criteria:
            return True
        
        max_education = criteria.get("education_max")
        if not max_education:
            return True
        
        # Simple string comparison (can be enhanced)
        return education.lower() <= max_education.lower()
