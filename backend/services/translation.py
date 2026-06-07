"""
Translation service for multi-language support.
"""
import hashlib
import logging
from typing import Optional

import httpx

from backend.config import settings
from backend.cache.redis_client import RedisClient, compute_hash


logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating text to Indian languages."""
    
    CACHE_TTL = 604800  # 7 days
    
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "mr": "Marathi",
        "gu": "Gujarati",
        "bn": "Bengali",
        "pa": "Punjabi",
        "or": "Odia",
        "as": "Assamese",
        "ur": "Urdu",
        "sa": "Sanskrit",
    }
    
    @staticmethod
    async def translate(text: str, target_language: str) -> str:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate.
            target_language: Target language code (e.g., 'ta', 'hi').
        
        Returns:
            Translated text or original if translation fails.
        """
        # Return original if target is English
        if target_language.lower() == "en":
            return text
        
        # Check cache
        text_hash = compute_hash(text)
        cache_key = f"trans:{text_hash}:{target_language}"
        cached = await RedisClient.get(cache_key)
        if cached:
            logger.debug(f"Translation cache hit: {cache_key}")
            return cached
        
        # Try IndicTrans microservice first
        translated = await TranslationService._translate_indictrans(text, target_language)
        if translated and translated != text:
            await RedisClient.set(cache_key, translated, TranslationService.CACHE_TTL)
            return translated
        
        # Fallback to Bhashini API
        translated = await TranslationService._translate_bhashini(text, target_language)
        if translated and translated != text:
            await RedisClient.set(cache_key, translated, TranslationService.CACHE_TTL)
            return translated
        
        # Return original text as final fallback
        logger.warning(f"Translation failed for {target_language}, returning original")
        return text
    
    @staticmethod
    async def _translate_indictrans(text: str, target_language: str) -> Optional[str]:
        """
        Translate using local IndicTrans microservice.
        
        Args:
            text: Text to translate.
            target_language: Target language code.
        
        Returns:
            Translated text or None.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    settings.indictrans_url,
                    json={
                        "text": text,
                        "source": "en",
                        "target": target_language
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("translated_text")
        except Exception as e:
            logger.debug(f"IndicTrans error: {str(e)}")
        
        return None
    
    @staticmethod
    async def _translate_bhashini(text: str, target_language: str) -> Optional[str]:
        """
        Translate using Bhashini API.
        
        Args:
            text: Text to translate.
            target_language: Target language code.
        
        Returns:
            Translated text or None.
        """
        if not settings.bhashini_api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://bhashini.gov.in/ulca/apis/v0/model/compute",
                    headers={"authorization": settings.bhashini_api_key},
                    json={
                        "task": "translation",
                        "domain": "general",
                        "language": {
                            "sourceLanguage": "en",
                            "targetLanguage": target_language
                        },
                        "input": {
                            "text": text
                        }
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    output = data.get("output", {})
                    return output.get("text")
        except Exception as e:
            logger.debug(f"Bhashini error: {str(e)}")
        
        return None
