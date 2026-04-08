import requests
import streamlit as st  # Add this import

# Change to your backend address if needed
API_BASE = "http://127.0.0.1:8000"

class APIError(Exception):
    pass

def _handle_response(resp):
    try:
        data = resp.json()
    except Exception:
        resp.raise_for_status()
    if resp.status_code >= 400:
        # FastAPI errors often have {"detail": "..."}
        detail = data.get("detail") if isinstance(data, dict) else None
        raise APIError(detail or f"HTTP {resp.status_code}")
    return data

def api_get(path, params=None):
    resp = requests.get(f"{API_BASE}{path}", params=params, timeout=10)
    return _handle_response(resp)

def api_post(path, payload):
    resp = requests.post(f"{API_BASE}{path}", json=payload, timeout=10)
    return _handle_response(resp)

def api_patch(path, payload):
    resp = requests.patch(f"{API_BASE}{path}", json=payload, timeout=10)
    return _handle_response(resp)

# convenience wrappers
def get_accounts():
    return api_get("/accounts")

def create_account(payload):
    return api_post("/accounts", payload)

def update_account(account_id, payload):
    return api_patch(f"/accounts/{account_id}", payload)

def get_opportunities(params=None):
    return api_get("/opportunities", params=params)

def create_opportunity(payload):
    return api_post("/opportunities", payload)

def update_opportunity(opportunity_id, payload):
    return api_patch(f"/opportunities/{opportunity_id}", payload)

def get_activities(params=None):
    return api_get("/activities", params=params)

def create_activity(payload):
    return api_post("/activities", payload)


# -------------------------
# API FUNCTIONS
# -------------------------

def get_users() -> list:
    """Get all users"""
    response = api_get("/users")
    
    # Ensure we always return a list
    if isinstance(response, dict):
        return response.get("data", [])
    return response or []


def get_user(user_id: int) -> dict:
    """Get a specific user"""
    return api_get(f"/users/{user_id}")


def create_user(payload: dict) -> dict:
    """Create a new user"""
    return api_post("/users", payload)


def create_user(payload: dict):
    return api_post("/users", payload)