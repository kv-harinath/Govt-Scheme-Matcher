"""
OTP service for authentication.
"""
import random
import logging
from typing import Optional

import httpx

from backend.config import settings
from backend.cache.redis_client import RedisClient


logger = logging.getLogger(__name__)


class OTPService:
    """Service for sending and verifying OTPs."""
    
    OTP_TTL = 600  # 10 minutes
    OTP_LENGTH = 6
    
    @staticmethod
    async def send_otp(phone: str) -> bool:
        """
        Send OTP via MSG91 or Fast2SMS.
        
        Args:
            phone: Phone number.
        
        Returns:
            True if OTP sent successfully.
        """
        otp = str(random.randint(100000, 999999))
        
        # Store in Redis
        cache_key = f"otp:{phone}"
        await RedisClient.set(cache_key, otp, OTPService.OTP_TTL)
        
        # Try MSG91 first
        if settings.msg91_api_key:
            try:
                success = await OTPService._send_via_msg91(phone, otp)
                if success:
                    logger.info(f"OTP sent via MSG91 to {phone}")
                    return True
            except Exception as e:
                logger.warning(f"MSG91 failed: {str(e)}")
        
        # Fallback to Fast2SMS
        if settings.fast2sms_api_key:
            try:
                success = await OTPService._send_via_fast2sms(phone, otp)
                if success:
                    logger.info(f"OTP sent via Fast2SMS to {phone}")
                    return True
            except Exception as e:
                logger.warning(f"Fast2SMS failed: {str(e)}")
        
        logger.error(f"Failed to send OTP to {phone}")
        return False
    
    @staticmethod
    async def _send_via_msg91(phone: str, otp: str) -> bool:
        """
        Send OTP via MSG91 API.
        
        Args:
            phone: Phone number.
            otp: OTP code.
        
        Returns:
            True if successful.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    "https://api.msg91.com/api/sendotp.php",
                    params={
                        "authkey": settings.msg91_api_key,
                        "mobile": phone,
                        "message": f"Your OTP is {otp}. Valid for 10 minutes.",
                        "sender": "GOVTAPP"
                    }
                )
                return response.status_code == 200
            except Exception as e:
                logger.error(f"MSG91 error: {str(e)}")
                return False
    
    @staticmethod
    async def _send_via_fast2sms(phone: str, otp: str) -> bool:
        """
        Send OTP via Fast2SMS API.
        
        Args:
            phone: Phone number.
            otp: OTP code.
        
        Returns:
            True if successful.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    "https://www.fast2sms.com/dev/bulkSms",
                    headers={"authorization": settings.fast2sms_api_key},
                    params={
                        "message": f"Your OTP is {otp}. Valid for 10 minutes.",
                        "language": "english",
                        "route": "otp",
                        "numbers": phone
                    }
                )
                return response.status_code == 200
            except Exception as e:
                logger.error(f"Fast2SMS error: {str(e)}")
                return False
    
    @staticmethod
    async def verify_otp(phone: str, otp: str) -> bool:
        """
        Verify OTP from cache.
        
        Args:
            phone: Phone number.
            otp: OTP to verify.
        
        Returns:
            True if OTP is valid and not expired.
        """
        cache_key = f"otp:{phone}"
        stored_otp = await RedisClient.get(cache_key)
        
        if stored_otp is None:
            logger.warning(f"OTP expired for {phone}")
            return False
        
        if stored_otp != otp:
            logger.warning(f"Invalid OTP for {phone}")
            return False
        
        # Delete OTP after successful verification
        await RedisClient.delete(cache_key)
        logger.info(f"OTP verified for {phone}")
        return True
