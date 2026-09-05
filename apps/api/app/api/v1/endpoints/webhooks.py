"""
Razorpay Webhook & Event Ingestion Endpoints for FraudLens
Secures incoming Razorpay Test Mode webhooks via HMAC SHA256 signature verification,
enforces idempotency, and channels both Razorpay and Synthetic events into
the unified intelligence pipeline.
"""

from fastapi import APIRouter, Request, Header, HTTPException, status, Response
from typing import Optional, Dict, Any
import json

from services.ingestion.models import PipelineProcessingResult, TransactionEvent
from services.ingestion.razorpay_adapter import RazorpayEventAdapter
from services.ingestion.pipeline import PipelineOrchestrator
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import AuthenticationFailedError, ValidationFailedError

router = APIRouter(tags=["Payment Webhooks & Ingestion"])


@router.post(
    "/webhooks/razorpay",
    response_model=PipelineProcessingResult,
    summary="Secure Razorpay Webhook Ingestion (Test Mode)",
)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
):
    """
    Ingests and validates incoming Razorpay Test Mode webhooks:
    1. Validates HMAC SHA256 signature against RAZORPAY_WEBHOOK_SECRET.
    2. Enforces idempotency to prevent double-processing.
    3. Normalizes payload into internal TransactionEvent.
    4. Routes event into unified ML and Graph processing pipeline.
    """
    raw_body = await request.body()

    # 1. Cryptographic Signature Validation
    if not x_razorpay_signature:
        logger.warning("Rejected webhook: Missing X-Razorpay-Signature header.")
        raise AuthenticationFailedError("Missing required X-Razorpay-Signature header.")

    is_valid = RazorpayEventAdapter.verify_webhook_signature(
        raw_body=raw_body,
        signature_header=x_razorpay_signature,
        secret=settings.RAZORPAY_WEBHOOK_SECRET,
    )
    if not is_valid:
        logger.warning("Rejected webhook: Invalid HMAC SHA256 signature.")
        raise AuthenticationFailedError("Invalid webhook signature for Razorpay Test Mode.")

    # 2. JSON Validation
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logger.warning(f"Rejected webhook: Malformed JSON payload ({e})")
        raise ValidationFailedError(f"Malformed JSON payload in webhook request: {e}")

    # 3. Normalize into internal TransactionEvent
    try:
        event = RazorpayEventAdapter.normalize_razorpay_payload(payload)
    except Exception as e:
        logger.error(f"Failed to normalize Razorpay webhook payload: {e}")
        raise ValidationFailedError(f"Unable to parse required transaction fields: {e}")

    # 4. Orchestrate Pipeline Execution
    orchestrator = PipelineOrchestrator.get_instance()
    result = orchestrator.process_event(event)

    return result


@router.post(
    "/events/synthetic",
    response_model=PipelineProcessingResult,
    summary="Ingest FraudLens Synthetic Universe Event (Demo Mode)",
)
async def handle_synthetic_event(payload: Dict[str, Any]):
    """
    Ingests a FraudLens synthetic transaction into the same core processing pipeline,
    clearly tagged with source_label: 'FraudLens Synthetic Event'.
    """
    event = RazorpayEventAdapter.normalize_synthetic_payload(payload)
    orchestrator = PipelineOrchestrator.get_instance()
    result = orchestrator.process_event(event)
    return result
