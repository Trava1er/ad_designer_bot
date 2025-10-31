"""
Stripe payment provider for USD payments.
"""

import asyncio
import hashlib
import hmac
import json
import uuid
from typing import Dict, Any, Optional
import httpx
import logging

from .base import BasePaymentProvider, PaymentResult, WebhookResult, PaymentStatus
from config import settings

logger = logging.getLogger(__name__)


class StripeProvider(BasePaymentProvider):
    """Stripe payment provider for USD payments."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Stripe provider."""
        config = config or {
            "secret_key": settings.stripe_secret_key,
            "publishable_key": settings.stripe_publishable_key,
            "webhook_secret": settings.stripe_webhook_secret,
            "api_url": "https://api.stripe.com/v1",
        }
        super().__init__(config)
        
        if not self.config.get("secret_key"):
            logger.warning("Stripe credentials not configured")
    
    def get_supported_currencies(self) -> list[str]:
        """Get supported currencies."""
        return ["USD"]
    
    async def create_invoice(self, user_id: int, amount: float, currency: str, description: str, **kwargs) -> PaymentResult:
        """Create Stripe payment session."""
        try:
            if not self.is_currency_supported(currency):
                return PaymentResult(
                    success=False,
                    error_message=f"Currency {currency} not supported by Stripe"
                )
            
            if not self.validate_amount(amount, currency):
                return PaymentResult(
                    success=False,
                    error_message=f"Invalid amount: {amount}"
                )
            
            # Convert amount to cents for Stripe
            amount_cents = int(amount * 100)
            
            # Create checkout session data
            session_data = {
                "payment_method_types": ["card"],
                "line_items": [{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": description,
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                "mode": "payment",
                "success_url": kwargs.get("success_url", "https://t.me/your_bot?success=1"),
                "cancel_url": kwargs.get("cancel_url", "https://t.me/your_bot?cancelled=1"),
                "metadata": {
                    "user_id": str(user_id),
                    "internal_payment_id": str(uuid.uuid4())
                }
            }
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {self.config['secret_key']}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            # Convert data to URL-encoded format for Stripe
            encoded_data = self._encode_stripe_data(session_data)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config['api_url']}/checkout/sessions",
                    data=encoded_data,
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                
                return PaymentResult(
                    success=True,
                    payment_url=result["url"],
                    payment_id=result["id"],
                    additional_data=result
                )
            else:
                logger.error(f"Stripe API error: {response.status_code} - {response.text}")
                return PaymentResult(
                    success=False,
                    error_message=f"Payment creation failed: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Stripe payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message=f"Payment creation error: {str(e)}"
            )
    
    def _encode_stripe_data(self, data: Dict[str, Any], prefix: str = "") -> str:
        """Encode data for Stripe API."""
        encoded_pairs = []
        
        for key, value in data.items():
            if prefix:
                full_key = f"{prefix}[{key}]"
            else:
                full_key = key
            
            if isinstance(value, dict):
                encoded_pairs.append(self._encode_stripe_data(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        encoded_pairs.append(self._encode_stripe_data(item, f"{full_key}[{i}]"))
                    else:
                        encoded_pairs.append(f"{full_key}[{i}]={item}")
            else:
                encoded_pairs.append(f"{full_key}={value}")
        
        return "&".join(encoded_pairs)
    
    async def verify_payment(self, data: Dict[str, Any]) -> WebhookResult:
        """Verify Stripe webhook."""
        try:
            # For Stripe, webhook verification should be done with signature
            # This is a simplified version
            event_type = data.get("type")
            event_data = data.get("data", {}).get("object", {})
            
            if event_type == "checkout.session.completed":
                payment_mode = event_data.get("payment_status")
                
                if payment_mode == "paid":
                    return WebhookResult(
                        is_valid=True,
                        payment_id=event_data.get("id"),
                        status=PaymentStatus.PAID,
                        amount=float(event_data.get("amount_total", 0)) / 100,  # Convert from cents
                        currency=event_data.get("currency", "").upper(),
                        transaction_id=event_data.get("payment_intent")
                    )
            
            return WebhookResult(
                is_valid=False,
                error_message=f"Unhandled event type: {event_type}"
            )
            
        except Exception as e:
            logger.error(f"Stripe webhook verification error: {e}")
            return WebhookResult(
                is_valid=False,
                error_message=f"Webhook verification error: {str(e)}"
            )
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify Stripe webhook signature."""
        try:
            webhook_secret = self.config.get("webhook_secret")
            if not webhook_secret:
                logger.warning("Stripe webhook secret not configured")
                return False
            
            # Extract timestamp and signatures from header
            elements = signature.split(",")
            timestamp = None
            signatures = []
            
            for element in elements:
                key, value = element.split("=", 1)
                if key == "t":
                    timestamp = value
                elif key == "v1":
                    signatures.append(value)
            
            if not timestamp or not signatures:
                return False
            
            # Create expected signature
            signed_payload = f"{timestamp}.{payload}"
            expected_sig = hmac.new(
                webhook_secret.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return any(hmac.compare_digest(expected_sig, sig) for sig in signatures)
            
        except Exception as e:
            logger.error(f"Stripe signature verification error: {e}")
            return False
    
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Get payment status from Stripe."""
        try:
            headers = {
                "Authorization": f"Bearer {self.config['secret_key']}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config['api_url']}/checkout/sessions/{payment_id}",
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                payment_status = result.get("payment_status")
                
                if payment_status == "paid":
                    return PaymentStatus.PAID
                elif payment_status == "unpaid":
                    return PaymentStatus.PENDING
                else:
                    return PaymentStatus.FAILED
            else:
                logger.error(f"Stripe status check error: {response.status_code}")
                return PaymentStatus.FAILED
                
        except Exception as e:
            logger.error(f"Stripe status check error: {e}")
            return PaymentStatus.FAILED
    
    async def health_check(self) -> bool:
        """Check Stripe API availability."""
        try:
            if not self.config.get("secret_key"):
                return False
                
            headers = {
                "Authorization": f"Bearer {self.config['secret_key']}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config['api_url']}/account",
                    headers=headers,
                    timeout=10.0
                )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Stripe health check error: {e}")
            return False