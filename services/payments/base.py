"""
Base payment provider abstract class.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class PaymentResult:
    """Payment operation result."""
    success: bool
    payment_url: Optional[str] = None
    payment_id: Optional[str] = None
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class WebhookResult:
    """Webhook verification result."""
    is_valid: bool
    payment_id: Optional[str] = None
    status: Optional[PaymentStatus] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None


class BasePaymentProvider(ABC):
    """Abstract base class for payment providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize payment provider with configuration."""
        self.config = config
        self.provider_name = self.__class__.__name__.lower()
    
    @abstractmethod
    async def create_invoice(self, user_id: int, amount: float, currency: str, description: str, **kwargs) -> PaymentResult:
        """
        Create payment invoice.
        
        Args:
            user_id: User identifier
            amount: Payment amount
            currency: Currency code (RUB, USD, USDT)
            description: Payment description
            **kwargs: Additional provider-specific parameters
            
        Returns:
            PaymentResult with payment URL and ID
        """
        pass
    
    @abstractmethod
    async def verify_payment(self, data: Dict[str, Any]) -> WebhookResult:
        """
        Verify payment webhook data.
        
        Args:
            data: Webhook payload data
            
        Returns:
            WebhookResult with verification status and payment info
        """
        pass
    
    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """
        Get current payment status.
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            Current payment status
        """
        pass
    
    async def cancel_payment(self, payment_id: str) -> bool:
        """
        Cancel payment (if supported by provider).
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            True if cancellation was successful
        """
        return False
    
    def get_supported_currencies(self) -> list[str]:
        """Get list of supported currencies."""
        return []
    
    def is_currency_supported(self, currency: str) -> bool:
        """Check if currency is supported."""
        return currency in self.get_supported_currencies()
    
    def validate_amount(self, amount: float, currency: str) -> bool:
        """Validate payment amount for currency."""
        if amount <= 0:
            return False
        
        # Basic validation, can be overridden in specific providers
        if currency == "RUB" and amount < 1:
            return False
        elif currency in ["USD", "USDT"] and amount < 0.01:
            return False
            
        return True
    
    def format_amount(self, amount: float, currency: str) -> str:
        """Format amount for display."""
        if currency == "RUB":
            return f"{amount:.2f} ₽"
        elif currency == "USD":
            return f"${amount:.2f}"
        elif currency == "USDT":
            return f"{amount:.6f} USDT"
        else:
            return f"{amount} {currency}"
    
    async def health_check(self) -> bool:
        """Check if payment provider is available."""
        return True
    
    def get_webhook_url(self, base_url: str) -> str:
        """Get webhook URL for this provider."""
        return f"{base_url}/webhook/{self.provider_name}"
    
    def log_transaction(self, transaction_data: Dict[str, Any]) -> None:
        """Log transaction for audit purposes."""
        # Implementation depends on logging strategy
        pass