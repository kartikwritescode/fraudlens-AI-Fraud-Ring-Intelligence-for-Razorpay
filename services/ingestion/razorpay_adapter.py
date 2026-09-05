"""
Razorpay Event Adapter for FraudLens
Isolates Razorpay Test Mode webhook parsing, HMAC SHA256 signature verification,
and normalization into internal TransactionEvent models.
"""

import hmac
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import hashlib

from services.ingestion.models import TransactionEvent
from app.core.config import settings


class RazorpayEventAdapter:
    """Isolates Razorpay webhook cryptographic verification and field translation."""

    @staticmethod
    def verify_webhook_signature(
        raw_body: bytes,
        signature_header: Optional[str],
        secret: Optional[str] = None,
    ) -> bool:
        """
        Validates the HMAC SHA256 signature sent in the X-Razorpay-Signature header.
        Uses constant-time comparison to prevent timing side-channel attacks.
        """
        if not signature_header or not raw_body:
            return False

        webhook_secret = secret or settings.RAZORPAY_WEBHOOK_SECRET
        if not webhook_secret:
            return False

        try:
            expected_signature = hmac.new(
                webhook_secret.encode("utf-8"),
                raw_body,
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(expected_signature, signature_header)
        except Exception:
            return False

    @staticmethod
    def normalize_razorpay_payload(payload: Dict[str, Any]) -> TransactionEvent:
        """
        Converts a raw Razorpay webhook payload into a normalized TransactionEvent.
        Handles paise-to-INR unit conversion and metadata extraction.
        """
        event_name = payload.get("event", "payment.authorized")
        event_id = payload.get("event_id")

        # Extract payment entity
        payment_entity = (
            payload.get("payload", {})
            .get("payment", {})
            .get("entity", {})
        )

        # Fallback to order entity if order.paid event
        if not payment_entity and "order" in payload.get("payload", {}):
            payment_entity = payload["payload"]["order"]["entity"]

        tx_id = payment_entity.get("id", f"pay_test_{datetime.now().timestamp()}")
        # Razorpay sends amount in paise (1 INR = 100 paise)
        raw_paise = payment_entity.get("amount", 0)
        amount_inr = round(float(raw_paise) / 100.0, 2)
        currency = payment_entity.get("currency", "INR")
        status = payment_entity.get("status", "authorized")
        if status == "captured":
            norm_status = "captured"
        elif status in ["failed", "blocked"]:
            norm_status = "failed"
        else:
            norm_status = "authorized"

        # Extract notes or metadata
        notes = payment_entity.get("notes", {}) or {}
        device_id = notes.get("device_id") or f"dev_rzp_{payment_entity.get('card_id', 'client')[-8:]}"
        ip_hash = notes.get("ip_hash") or f"ip_rzp_{hashlib.sha256(payment_entity.get('email', 'guest').encode()).hexdigest()[:10]}"
        token_hash = notes.get("token_hash") or payment_entity.get("token_id") or f"tok_rzp_{payment_entity.get('card_id', 'inst')}"

        email = payment_entity.get("email", "customer@example.com")
        phone = payment_entity.get("contact", "+919876543210")
        email_hash = f"em_{hashlib.sha256(email.encode()).hexdigest()[:12]}"
        phone_hash = f"ph_{hashlib.sha256(phone.encode()).hexdigest()[:12]}"

        cust_id = payment_entity.get("customer_id") or f"cust_rzp_{email_hash[-8:]}"
        merchant_id = notes.get("merchant_id", "mer_razorpay_test")
        method = payment_entity.get("method", "card")

        # Timestamp
        created_at_epoch = payment_entity.get("created_at")
        if created_at_epoch:
            ts_str = datetime.fromtimestamp(created_at_epoch, tz=timezone.utc).isoformat()
        else:
            ts_str = datetime.now(timezone.utc).isoformat()

        return TransactionEvent(
            event_id=event_id or f"evt_{tx_id[-8:]}",
            source_mode="RAZORPAY_TEST_MODE",
            source_label="Razorpay Test Event",
            event_type=event_name,
            transaction_id=tx_id,
            amount=amount_inr,
            currency=currency,
            status=norm_status,
            customer_id=cust_id,
            merchant_id=merchant_id,
            payment_method=method,
            device_id=device_id,
            ip_hash=ip_hash,
            payment_token_hash=token_hash,
            email_hash=email_hash,
            phone_hash=phone_hash,
            billing_country=notes.get("billing_country", "IND"),
            shipping_country=notes.get("shipping_country", "IND"),
            order_id=payment_entity.get("order_id"),
            raw_payload=payload,
            timestamp=ts_str,
        )

    @staticmethod
    def normalize_synthetic_payload(tx: Dict[str, Any]) -> TransactionEvent:
        """
        Normalizes a FraudLens synthetic universe transaction for ingestion through the same pipeline.
        """
        tid = tx.get("transaction_id", f"tx_synth_{datetime.now().timestamp()}")
        return TransactionEvent(
            event_id=f"evt_synth_{tid[-10:]}",
            source_mode="FRAUDLENS_DEMO_MODE",
            source_label="FraudLens Synthetic Event",
            event_type="payment.authorized",
            transaction_id=tid,
            amount=float(tx.get("amount", 0.0)),
            currency=tx.get("currency", "INR"),
            status=tx.get("status", "captured"),
            customer_id=tx.get("customer_id", "cust_unknown"),
            merchant_id=tx.get("merchant_id", "mer_unknown"),
            payment_method=tx.get("payment_method", "upi"),
            device_id=tx.get("device_id", "dev_unknown"),
            ip_hash=tx.get("ip_hash", "ip_unknown"),
            payment_token_hash=tx.get("payment_token_hash", "tok_unknown"),
            email_hash=tx.get("email_hash", ""),
            phone_hash=tx.get("phone_hash", ""),
            billing_country=tx.get("billing_country", "IND"),
            shipping_country=tx.get("shipping_country", "IND"),
            order_id=tx.get("order_id"),
            raw_payload=tx,
            timestamp=tx.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )
