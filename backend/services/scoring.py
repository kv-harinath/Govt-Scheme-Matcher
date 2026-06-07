"""
Scoring and ranking service for matched schemes.
"""
import logging
from typing import List, Dict, Any

from backend.models.scheme import Scheme
from backend.models.user import UserProfile
from backend.schemas.match import MatchResult


logger = logging.getLogger(__name__)


class ScoringService:
    """Service for scoring and ranking matched schemes."""
    
    MAX_RESULTS = 20
    
    @staticmethod
    def score_and_rank(
        schemes: List[Scheme],
        groq_results: Dict[str, Dict[str, Any]],
        profile: UserProfile
    ) -> List[MatchResult]:
        """
        Score and rank matched schemes.
        
        Args:
            schemes: List of eligible schemes from rule engine.
            groq_results: Dict of scheme_id -> groq evaluation result.
            profile: User profile.
        
        Returns:
            Sorted list of MatchResult objects (top MAX_RESULTS).
        """
        match_results = []
        
        for scheme in schemes:
            score = ScoringService._calculate_score(scheme, groq_results, profile)
            
            groq_result = groq_results.get(str(scheme.id), {})
            
            match_result = MatchResult(
                scheme_id=scheme.id,
                scheme_name=scheme.name,
                category=scheme.category or [],
                level=scheme.level,
                state=scheme.state,
                score=score,
                match_reason=f"Eligible for {scheme.name}",
                eligibility_reason=scheme.eligibility_criteria.get("custom_rules", []),
                confidence=groq_result.get("confidence", 1.0),
                application_mode=scheme.application_mode,
                application_url=scheme.application_url,
                required_documents=scheme.required_documents or [],
                benefits=scheme.benefits
            )
            match_results.append(match_result)
        
        # Sort by score (descending)
        match_results.sort(key=lambda x: x.score, reverse=True)
        
        # Return top MAX_RESULTS
        return match_results[:ScoringService.MAX_RESULTS]
    
    @staticmethod
    def _calculate_score(
        scheme: Scheme,
        groq_results: Dict[str, Dict[str, Any]],
        profile: UserProfile
    ) -> float:
        """
        Calculate match score for a scheme.
        
        Scoring formula:
        - Base: 1.0
        - +0.2 if scheme category matches profile interests
        - +groq_confidence * 0.1 (if custom rules evaluated)
        - +0.1 if application_mode == 'online'
        - -0.1 if application_mode == 'offline'
        
        Args:
            scheme: Scheme to score.
            groq_results: Groq evaluation results.
            profile: User profile.
        
        Returns:
            Score between 0.0 and 1.0.
        """
        score = 1.0
        
        # Category match bonus
        if scheme.category and ScoringService._has_category_interest(profile):
            score += 0.2
        
        # Groq confidence bonus
        groq_result = groq_results.get(str(scheme.id))
        if groq_result:
            confidence = groq_result.get("confidence", 0.5)
            score += confidence * 0.1
        
        # Application mode bonus/penalty
        if scheme.application_mode == "online":
            score += 0.1
        elif scheme.application_mode == "offline":
            score -= 0.1
        
        # Ensure score is between 0 and 1.1 (small overage allowed for bonuses)
        return max(0.0, min(1.1, score))
    
    @staticmethod
    def _has_category_interest(profile: UserProfile) -> bool:
        """
        Check if user has interests matching scheme categories.
        
        Args:
            profile: User profile.
        
        Returns:
            True if profile indicates interest.
        """
        # Profile-based category matching
        if profile.occupation == "farmer":
            return True
        if profile.disability:
            return True
        if profile.marital_status == "widow":
            return True
        if profile.caste in ["SC", "ST", "OBC"]:
            return True
        
        return False
