"""Tests for authentication endpoints."""

import pytest
import pytest_asyncio
from uuid import uuid4

from backend.auth.jwt_handler import create_access_token, decode_token


def test_create_token():
    """Test JWT token creation."""
    user_id = uuid4()
    token = create_access_token(user_id)
    assert token is not None
    assert isinstance(token, str)


def test_decode_token():
    """Test JWT token decoding."""
    user_id = uuid4()
    token = create_access_token(user_id)
    decoded_id = decode_token(token)
    assert decoded_id == user_id


def test_decode_invalid_token():
    """Test decoding invalid token."""
    from fastapi import HTTPException
    
    with pytest.raises(HTTPException):
        decode_token("invalid.token.here")


def test_decode_expired_token():
    """Test decoding expired token."""
    from datetime import timedelta
    from fastapi import HTTPException
    
    # Create token with negative expiry (already expired)
    user_id = uuid4()
    token = create_access_token(user_id, timedelta(hours=-1))
    
    with pytest.raises(HTTPException):
        decode_token(token)
