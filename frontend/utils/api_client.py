import os
from typing import Optional, List, Dict

import requests
import streamlit as st


# Base backend URL
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _auth_header(token: str) -> Dict[str, str]:
    """Return Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"} if token else {}


def _handle_request(fn_name: str, exc: Exception) -> None:
    """Show a friendly error in Streamlit for failed requests."""
    st.error(f"{fn_name} failed: {str(exc)}")


def send_otp(phone: str) -> Optional[Dict]:
    """Send OTP to a phone number. Returns response dict or None on failure."""
    url = f"{BASE_URL}/auth/send-otp"
    try:
        with st.spinner("Sending OTP..."):
            resp = requests.post(url, json={"phone": phone}, timeout=10)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        _handle_request("send_otp", e)
        return None


def verify_otp(phone: str, otp: str) -> Optional[Dict]:
    """Verify OTP and return tokens (e.g., {"token":..., "user_id":...})."""
    url = f"{BASE_URL}/auth/verify-otp"
    try:
        with st.spinner("Verifying OTP..."):
            resp = requests.post(url, json={"phone": phone, "otp": otp}, timeout=10)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        _handle_request("verify_otp", e)
        return None


def save_profile(user_id: str, profile: Dict, token: str) -> Optional[Dict]:
    """Save or update a user profile. Returns saved profile or None on failure."""
    url = f"{BASE_URL}/profile"
    headers = _auth_header(token)
    try:
        with st.spinner("Saving profile..."):
            payload = {"user_id": user_id, **profile}
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        _handle_request("save_profile", e)
        return None


@st.cache_data(ttl=300)
def get_profile(user_id: str, token: str) -> Optional[Dict]:
    """Retrieve a user profile. Cached for 5 minutes."""
    url = f"{BASE_URL}/profile/{user_id}"
    headers = _auth_header(token)
    try:
        with st.spinner("Loading profile..."):
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        _handle_request("get_profile", e)
        return None


def get_matches(user_id: str, token: str) -> Optional[List[Dict]]:
    """Run matching for a user and return a list of matched schemes."""
    url = f"{BASE_URL}/match"
    headers = _auth_header(token)
    try:
        with st.spinner("Finding schemes..."):
            resp = requests.post(url, json={"user_id": user_id}, headers=headers, timeout=20)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        _handle_request("get_matches", e)
        return None


@st.cache_data(ttl=300)
def get_schemes(category: Optional[str] = None, state: Optional[str] = None, page: int = 1) -> Optional[Dict]:
    """Fetch schemes list with optional filters. Cached for 5 minutes."""
    url = f"{BASE_URL}/schemes"
    params = {"page": page}
    if category:
        params["category"] = category
    if state:
        params["state"] = state
    try:
        with st.spinner("Loading schemes..."):
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        _handle_request("get_schemes", e)
        return None


@st.cache_data(ttl=300)
def get_scheme_detail(scheme_id: str) -> Optional[Dict]:
    """Fetch details for a single scheme. Cached for 5 minutes."""
    url = f"{BASE_URL}/schemes/{scheme_id}"
    try:
        with st.spinner("Loading scheme details..."):
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        _handle_request("get_scheme_detail", e)
        return None


@st.cache_data(ttl=300)
def search_schemes(query: str) -> Optional[List[Dict]]:
    """Search schemes by query string. Cached for 5 minutes."""
    url = f"{BASE_URL}/schemes/search"
    params = {"q": query}
    try:
        with st.spinner("Searching schemes..."):
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        _handle_request("search_schemes", e)
        return None


def translate_text(text: str, target_lang: str, token: str) -> Optional[str]:
    """Translate text to target language using backend translation endpoint."""
    url = f"{BASE_URL}/translate"
    headers = _auth_header(token)
    try:
        with st.spinner("Translating..."):
            resp = requests.post(url, json={"text": text, "target_language": target_lang}, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # Expecting {'translated_text': '...'} or a simple string
            if isinstance(data, dict):
                return data.get("translated_text") or data.get("text") or data.get("translation")
            if isinstance(data, str):
                return data
            return None
    except Exception as e:
        _handle_request("translate_text", e)
        return None
