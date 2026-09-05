"""
Analyst Authentication & Role-Based Access Control
Enforces credential verification on sensitive management and decision routes.
"""

from typing import Optional
from fastapi import Header, HTTPException, status
from app.core.config import settings
from app.core.errors import AuthenticationFailedError

VALID_ANALYST_KEYS = {
    "fraudlens_demo_analyst_2026": {"analyst_id": "lead_analyst_42", "role": "LEAD_RISK_ANALYST"},
    "fraudlens_master_key_99": {"analyst_id": "security_admin_01", "role": "SECURITY_ADMIN"},
}


async def verify_analyst_auth(
    x_analyst_key: Optional[str] = Header(None, alias="X-Analyst-Key"),
    authorization: Optional[str] = Header(None),
) -> dict:
    """
    Verifies that the caller possesses valid analyst credentials.
    Supports either X-Analyst-Key header or Authorization: Bearer <token>.
    In development mode, allows missing headers for streamlined local developer workflow.
    """
    token = None
    if x_analyst_key:
        token = x_analyst_key.strip()
    elif authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()

    if token:
        if token in VALID_ANALYST_KEYS:
            return VALID_ANALYST_KEYS[token]
        raise AuthenticationFailedError("Invalid or revoked analyst credentials.")

    # Graceful fallback for local development & simulation mode
    if settings.APP_ENV == "development":
        return {"analyst_id": "demo_analyst_01", "role": "ANALYST_DEV_MODE"}

    raise AuthenticationFailedError("Missing required analyst authentication header.")
