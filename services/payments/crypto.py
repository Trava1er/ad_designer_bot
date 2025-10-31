"""
Crypto payment provider for USDT payments using NOWPayments.
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


class CryptoProvider(BasePaymentProvider):
    """NOWPayments crypto provider for USDT payments."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize crypto provider."""
        config = config or {
            "api_key": settings.nowpayments_api_key,
            "ipn_secret": settings.nowpayments_ipn_secret,
            "api_url": "https://api.nowpayments.io/v1",
            "sandbox": False,  # Set to True for testing
        }
        super().__init__(config)
        
        if not self.config.get("api_key"):
            logger.warning("NOWPayments API key not configured")
    
    def get_supported_currencies(self) -> list[str]:
        """Get supported currencies."""
        return ["USDT"]
    
    async def create_invoice(self, user_id: int, amount: float, currency: str, description: str, **kwargs) -> PaymentResult:
        """Create crypto payment."""
        try:
            if not self.is_currency_supported(currency):
                return PaymentResult(
                    success=False,
                    error_message=f"Currency {currency} not supported by crypto provider"
                )
            
            if not self.validate_amount(amount, currency):
                return PaymentResult(
                    success=False,
                    error_message=f"Invalid amount: {amount}"
                )
            
            # Generate unique order ID
            order_id = f"ad_{user_id}_{uuid.uuid4().hex[:8]}"
            
            # Create payment data
            payment_data = {
                "price_amount": amount,
                "price_currency": "USD",  # Base currency
                "pay_currency": currency.lower(),  # Payment currency
                "ipn_callback_url": kwargs.get("webhook_url"),
                "order_id": order_id,
                "order_description": description,
                "purchase_id": str(uuid.uuid4()),
                "payout_address": None,  # Will be set to default
                "payout_currency": None,
                "payout_extra_id": None,
                "fixed_rate": True,
                "is_fee_paid_by_user": False,
            }
            
            # Make API request
            headers = {
                "x-api-key": self.config["api_key"],
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.config['api_url']}/payment",
                    json=payment_data,
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 201:
                result = response.json()
                
                return PaymentResult(
                    success=True,
                    payment_url=result.get("invoice_url"),
                    payment_id=str(result.get("payment_id")),
                    additional_data={
                        "order_id": order_id,
                        "pay_address": result.get("pay_address"),
                        "pay_amount": result.get("pay_amount"),
                        "pay_currency": result.get("pay_currency"),
                        "payment_id": result.get("payment_id"),
                        "network": result.get("network"),
                    }
                )
            else:
                logger.error(f"NOWPayments API error: {response.status_code} - {response.text}")
                return PaymentResult(
                    success=False,
                    error_message=f"Payment creation failed: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Crypto payment creation error: {e}")
            return PaymentResult(
                success=False,
                error_message=f"Payment creation error: {str(e)}"
            )
    
    async def verify_payment(self, data: Dict[str, Any]) -> WebhookResult:
        """Verify crypto payment webhook."""
        try:
            # Verify IPN signature if secret is configured
            if self.config.get("ipn_secret"):
                if not self._verify_ipn_signature(data):
                    return WebhookResult(
                        is_valid=False,
                        error_message="Invalid IPN signature"
                    )
            
            # Extract payment information
            payment_status = data.get("payment_status")
            payment_id = data.get("payment_id")
            order_id = data.get("order_id")
            pay_amount = data.get("pay_amount")
            pay_currency = data.get("pay_currency")
            outcome_amount = data.get("outcome_amount")
            outcome_currency = data.get("outcome_currency")
            
            # Map NOWPayments status to our status
            status_mapping = {
                "waiting": PaymentStatus.PENDING,
                "confirming": PaymentStatus.PENDING,
                "confirmed": PaymentStatus.PAID,
                "sending": PaymentStatus.PAID,
                "partially_paid": PaymentStatus.PENDING,
                "finished": PaymentStatus.PAID,
                "failed": PaymentStatus.FAILED,
                "refunded": PaymentStatus.CANCELLED,
                "expired": PaymentStatus.EXPIRED,
            }
            
            status = status_mapping.get(payment_status, PaymentStatus.FAILED)
            
            return WebhookResult(
                is_valid=True,
                payment_id=str(payment_id),
                status=status,
                amount=float(outcome_amount or pay_amount or 0),
                currency=(outcome_currency or pay_currency or "").upper(),
                transaction_id=data.get("txid")
            )
            
        except Exception as e:
            logger.error(f"Crypto webhook verification error: {e}")
            return WebhookResult(
                is_valid=False,
                error_message=f"Webhook verification error: {str(e)}"
            )
    
    def _verify_ipn_signature(self, data: Dict[str, Any]) -> bool:
        """Verify NOWPayments IPN signature."""
        try:
            received_signature = data.get("ipn_signature")
            if not received_signature:
                return False
            
            # Remove signature from data for verification
            verification_data = data.copy()
            verification_data.pop("ipn_signature", None)
            
            # Sort data by keys and create string
            sorted_data = sorted(verification_data.items())
            data_string = json.dumps(dict(sorted_data), separators=(',', ':'))
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.config["ipn_secret"].encode(),
                data_string.encode(),
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, received_signature)
            
        except Exception as e:
            logger.error(f"IPN signature verification error: {e}")
            return False
    
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Get payment status from NOWPayments."""
        try:
            headers = {
                "x-api-key": self.config["api_key"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config['api_url']}/payment/{payment_id}",
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                payment_status = result.get("payment_status")
                
                status_mapping = {
                    "waiting": PaymentStatus.PENDING,
                    "confirming": PaymentStatus.PENDING,
                    "confirmed": PaymentStatus.PAID,
                    "sending": PaymentStatus.PAID,
                    "partially_paid": PaymentStatus.PENDING,
                    "finished": PaymentStatus.PAID,
                    "failed": PaymentStatus.FAILED,
                    "refunded": PaymentStatus.CANCELLED,
                    "expired": PaymentStatus.EXPIRED,
                }
                
                return status_mapping.get(payment_status, PaymentStatus.FAILED)
            else:
                logger.error(f"NOWPayments status check error: {response.status_code}")
                return PaymentStatus.FAILED
                
        except Exception as e:
            logger.error(f"Crypto status check error: {e}")
            return PaymentStatus.FAILED
    
    async def get_available_currencies(self) -> list[str]:
        """Get list of available cryptocurrencies."""
        try:
            headers = {
                "x-api-key": self.config["api_key"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config['api_url']}/currencies",
                    headers=headers,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                return [currency["code"].upper() for currency in result.get("currencies", [])]
            else:
                logger.error(f"NOWPayments currencies error: {response.status_code}")
                return ["USDT"]  # Fallback
                
        except Exception as e:
            logger.error(f"Get currencies error: {e}")
            return ["USDT"]  # Fallback
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get exchange rate between currencies."""
        try:
            headers = {
                "x-api-key": self.config["api_key"]
            }
            
            params = {
                "from_currency": from_currency.lower(),
                "to_currency": to_currency.lower()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config['api_url']}/exchange-amount",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
            
            if response.status_code == 200:
                result = response.json()
                return float(result.get("estimated_amount", 0))
            else:
                return None
                
        except Exception as e:
            logger.error(f"Exchange rate error: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check NOWPayments API availability."""
        try:
            if not self.config.get("api_key"):
                return False
                
            headers = {
                "x-api-key": self.config["api_key"]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.config['api_url']}/status",
                    headers=headers,
                    timeout=10.0
                )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Crypto health check error: {e}")
            return False