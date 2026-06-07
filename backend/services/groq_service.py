"""
Groq LLM service for evaluating custom eligibility rules.
"""
import json
import logging
from typing import Dict, Any

from groq import Groq, RateLimitError

from backend.config import settings
from backend.cache.redis_client import RedisClient, compute_hash
from backend.models.scheme import Scheme
from backend.models.user import UserProfile


logger = logging.getLogger(__name__)


class GroqService:
    """Service for LLM-based eligibility evaluation."""
    
    CACHE_TTL = 86400  # 24 hours
    
    def __init__(self):
        """Initialize Groq client."""
        self.client = Groq(api_key=settings.groq_api_key)
    
    async def evaluate_custom_rules(
        self,
        profile: UserProfile,
        scheme: Scheme,
        profile_hash: str
    ) -> Dict[str, Any]:
        """
        Evaluate custom eligibility rules using Groq LLM.
        
        Args:
            profile: User profile.
            scheme: Scheme to evaluate.
            profile_hash: MD5 hash of profile.
        
        Returns:
            Dict with eligible (bool), reason (str), confidence (float).
        """
        custom_rules = scheme.eligibility_criteria.get("custom_rules", [])
        
        if not custom_rules:
            return {
                "eligible": True,
                "reason": "No custom rules to evaluate",
                "confidence": 1.0
            }
        
        # Check cache
        cache_key = f"groq:{scheme.id}:{profile_hash}"
        cached_result = await RedisClient.get_json(cache_key)
        if cached_result:
            logger.debug(f"Cache hit for Groq evaluation: {cache_key}")
            return cached_result
        
        # Prepare profile and scheme data
        profile_data = {
            "age": profile.age,
            "gender": profile.gender,
            "state": profile.state,
            "annual_income": profile.annual_income,
            "caste": profile.caste,
            "occupation": profile.occupation,
            "education": profile.education,
            "bpl_card": profile.bpl_card,
            "disability": profile.disability,
            "disability_type": profile.disability_type,
            "land_holding": profile.land_holding,
            "marital_status": profile.marital_status,
            "owns_house": profile.owns_house,
            "jan_dhan_account": profile.jan_dhan_account,
        }
        
        prompt = f"""You are an expert eligibility checker for Indian government schemes.
Your task is to evaluate whether a citizen is eligible for a specific scheme based on custom conditions.

Citizen Profile:
{json.dumps(profile_data, indent=2)}

Scheme: {scheme.name}
Custom Eligibility Conditions:
{json.dumps(custom_rules, indent=2)}

Evaluate the citizen's eligibility based on ALL custom conditions provided.
Be strict: if any condition is not met, mark as ineligible.

Return ONLY a valid JSON object (no markdown, no extra text):
{{
    "eligible": true or false,
    "reason": "Plain English explanation of decision",
    "confidence": 0.0 to 1.0 (your confidence in this assessment)
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an eligibility checker for Indian government schemes. Respond ONLY with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON if wrapped in markdown code blocks
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Validate response structure
            if "eligible" not in result or "reason" not in result or "confidence" not in result:
                logger.warning(f"Invalid Groq response structure: {result}")
                result = {
                    "eligible": True,
                    "reason": "Unable to parse response, defaulting to eligible",
                    "confidence": 0.5
                }
            
            # Ensure confidence is between 0 and 1
            result["confidence"] = max(0.0, min(1.0, float(result.get("confidence", 0.5))))
            
            # Cache result
            await RedisClient.set_json(cache_key, result, self.CACHE_TTL)
            
            logger.info(f"Groq evaluation: scheme={scheme.name}, eligible={result['eligible']}")
            return result
            
        except RateLimitError:
            logger.warning("Groq rate limit exceeded, returning fallback")
            fallback = {
                "eligible": True,
                "reason": "Rate limit reached, defaulting to eligible",
                "confidence": 0.5
            }
            # Don't cache fallback
            return fallback
        
        except Exception as e:
            logger.error(f"Groq evaluation error: {str(e)}")
            fallback = {
                "eligible": True,
                "reason": "Evaluation error, defaulting to eligible",
                "confidence": 0.5
            }
            return fallback
