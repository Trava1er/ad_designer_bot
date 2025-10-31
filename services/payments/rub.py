"""
Yookassa payment provider for RUB payments.
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


class YookassaProvider(BasePaymentProvider):
    """Yookassa payment provider for RUB payments."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Yookassa provider."""
        config = config or {
            "shop_id": settings.yookassa_shop_id,
            "secret_key": settings.yookassa_secret_key,
            "api_url": "https://api.yookassa.ru/v3",
        }
        super().__init__(config)
        
        if not self.config.get("shop_id") or not self.config.get("secret_key"):
            logger.warning("Yookassa credentials not configured")
    
    def get_supported_currencies(self) -> list[str]:
        """Get supported currencies."""
        return ["RUB"]
    
    async def create_invoice(self, user_id: int, amount: float, currency: str, description: str, **kwargs) -> PaymentResult:
        """Create Yookassa payment."""
        try:
            if not self.is_currency_supported(currency):
                return PaymentResult(
                    success=False,
                    error_message=f"Currency {currency} not supported by Yookassa"
                )
            
            if not self.validate_amount(amount, currency):
                return PaymentResult(
                    success=False,
                    error_message=f"Invalid amount: {amount}"
                )
            
            # Generate unique payment ID
            payment_id = str(uuid.uuid4())
            
            # Prepare payment data
            payment_data = {
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": currency
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": kwargs.get("return_url", "https://t.me/your_bot")
                },
                "capture": True,
                "description": description,
                "metadata": {
                    "user_id": str(user_id),
                    "internal_payment_id": payment_id
                }
            }
            
            # Make API request
            headers = {
                "Content-Type": "application/json",
                "Idempotence-Key": payment_id
            }
            
            auth = (self.config["shop_id"], self.config["secret_key"])
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config['api_url']}/payments",
                    json=payment_data,
                    headers=headers,
                    auth=auth,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                confirmation_url = result.get("confirmation", {}).get("confirmation_url")
                
                return PaymentResult(
                    success=True,
                    payment_url=confirmation_url,
                    payment_id=result["id"],
                    additional_data=result
                )
            else:
                logger.error(f"Yookassa API error: {response.status_code} - {response.text}")
                return PaymentResult(
                    success=False,
                    error_message=f"Payment creation failed: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Yookassa payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message=f"Payment creation error: {str(e)}"
            )
    
    async def verify_payment(self, data: Dict[str, Any]) -> WebhookResult:
        """Verify Yookassa webhook."""
        try:
            # Get event data
            event_type = data.get("event")
            payment_data = data.get("object", {})
            
            if event_type != "payment.succeeded":
                return WebhookResult(
                    is_valid=False,
                    error_message=f"Unhandled event type: {event_type}"
                )
            
            # Extract payment information
            payment_id = payment_data.get("id")
            status_str = payment_data.get("status")
            amount_data = payment_data.get("amount", {})
            
            # Map Yookassa status to our status
            status_mapping = {
                "succeeded": PaymentStatus.PAID,
                "pending": PaymentStatus.PENDING,
                "canceled": PaymentStatus.CANCELLED,
                "waiting_for_capture": PaymentStatus.PENDING
            }
            
            status = status_mapping.get(status_str, PaymentStatus.FAILED)
            
            return WebhookResult(
                is_valid=True,
                payment_id=payment_id,
                status=status,
                amount=float(amount_data.get("value", 0)),
                currency=amount_data.get("currency"),
                transaction_id=payment_id
            )
            
        except Exception as e:
            logger.error(f"Yookassa webhook verification error: {e}")
            return WebhookResult(
                is_valid=False,
                error_message=f"Webhook verification error: {str(e)}"
            )
    
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Get payment status from Yookassa."""
        try:
            auth = (self.config["shop_id"], self.config["secret_key"])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config['api_url']}/payments/{payment_id}",
                    auth=auth,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                status_str = result.get("status")
                
                status_mapping = {
                    "succeeded": PaymentStatus.PAID,
                    "pending": PaymentStatus.PENDING,
                    "canceled": PaymentStatus.CANCELLED,
                    "waiting_for_capture": PaymentStatus.PENDING
                }
                
                return status_mapping.get(status_str, PaymentStatus.FAILED)
            else:
                logger.error(f"Yookassa status check error: {response.status_code}")
                return PaymentStatus.FAILED
                
        except Exception as e:
            logger.error(f"Yookassa status check error: {e}")
            return PaymentStatus.FAILED
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """Cancel Yookassa payment."""
        try:
            auth = (self.config["shop_id"], self.config["secret_key"])
            
            cancel_data = {
                "payment_id": payment_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config['api_url']}/payments/{payment_id}/cancel",
                    json=cancel_data,
                    auth=auth,
                    timeout=30.0
                )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Yookassa payment cancellation error: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Yookassa API availability."""
        try:
            if not self.config.get("shop_id") or not self.config.get("secret_key"):
                return False
                
            auth = (self.config["shop_id"], self.config["secret_key"])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config['api_url']}/me",
                    auth=auth,
                    timeout=10.0
                )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Yookassa health check error: {e}")
            return False