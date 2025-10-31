"""
Configuration module for AdDesigner Hub bot.
Uses pydantic-settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Bot configuration
    telegram_bot_token: str = Field(..., description="Telegram bot token from BotFather")
    admin_id: int = Field(..., description="Admin Telegram user ID")
    bot_username: str = Field(default="AdDesignerHubBot", description="Bot username")
    
    # Database
    database_url: str = Field(default="sqlite:///./app.db", description="Database connection URL")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key for text/image generation")
    openai_model: str = Field(default="gpt-3.5-turbo", description="OpenAI model for text generation")
    openai_image_model: str = Field(default="dall-e-3", description="OpenAI model for image generation")
    openai_max_tokens: int = Field(default=1000, description="Max tokens for OpenAI text generation")
    
    # Default channel
    channel_id_default: int = Field(..., description="Default channel ID for posting ads")
    
    # Payment providers
    # RUB payments (Yookassa)
    yookassa_shop_id: Optional[str] = Field(default=None, description="Yookassa shop ID")
    yookassa_secret_key: Optional[str] = Field(default=None, description="Yookassa secret key")
    
    # USD payments (Stripe)
    stripe_publishable_key: Optional[str] = Field(default=None, description="Stripe publishable key")
    stripe_secret_key: Optional[str] = Field(default=None, description="Stripe secret key")
    stripe_webhook_secret: Optional[str] = Field(default=None, description="Stripe webhook secret")
    
    # Crypto payments (NOWPayments)
    nowpayments_api_key: Optional[str] = Field(default=None, description="NOWPayments API key")
    nowpayments_ipn_secret: Optional[str] = Field(default=None, description="NOWPayments IPN secret")
    
    # Application settings
    webhook_url: Optional[str] = Field(default=None, description="Webhook URL for payment callbacks")
    webhook_path: str = Field(default="/webhook", description="Webhook path")
    webhook_port: int = Field(default=8080, description="Webhook port")
    
    # Features toggles
    enable_openai_text: bool = Field(default=True, description="Enable OpenAI text generation")
    enable_openai_images: bool = Field(default=True, description="Enable OpenAI image generation")
    enable_receipts: bool = Field(default=True, description="Enable PDF receipt generation")
    
    # Limits
    max_ad_text_length: int = Field(default=4000, description="Maximum ad text length")
    max_media_files: int = Field(default=10, description="Maximum media files per ad")
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    
    # Receipt settings
    company_name: str = Field(default="AdDesigner Hub", description="Company name for receipts")
    company_address: str = Field(default="", description="Company address for receipts")
    company_phone: str = Field(default="", description="Company phone for receipts")
    company_email: str = Field(default="", description="Company email for receipts")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(default="logs/bot.log", description="Log file path")
    
    # Redis (optional, for caching)
    redis_url: Optional[str] = Field(default=None, description="Redis URL for caching")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create settings instance
settings = Settings()


# Constants
class Currency:
    """Supported currencies."""
    RUB = "RUB"
    USD = "USD" 
    USDT = "USDT"
    
    ALL = [RUB, USD, USDT]


class PaymentProvider:
    """Payment provider identifiers."""
    YOOKASSA = "yookassa"
    STRIPE = "stripe"
    CRYPTO = "crypto"
    TELEGRAM = "telegram"


class Language:
    """Supported languages."""
    RU = "ru"
    EN = "en"
    ZH_TW = "zh-tw"
    
    ALL = [RU, EN, ZH_TW]
    DEFAULT = RU


class AdStatus:
    """Advertisement status values."""
    DRAFT = "draft"
    WAITING_PAYMENT = "waiting_payment"
    WAITING_MODERATION = "waiting_moderation"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    
    ALL = [DRAFT, WAITING_PAYMENT, WAITING_MODERATION, APPROVED, REJECTED, PUBLISHED]


class PaymentStatus:
    """Payment status values."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    
    ALL = [PENDING, PAID, FAILED, EXPIRED, CANCELLED]


# Emoji constants
class Emoji:
    """Commonly used emojis."""
    CHECK = "✅"
    CROSS = "❌"
    EDIT = "📝"
    IMAGE = "🖼"
    MONEY = "💰"
    CLOCK = "🕐"
    WARNING = "⚠️"
    INFO = "ℹ️"
    STAR = "⭐"
    FIRE = "🔥"
    THUMBS_UP = "👍"
    THUMBS_DOWN = "👎"
    BACK = "🔙"
    FORWARD = "▶️"
    REFRESH = "🔄"
    SETTINGS = "⚙️"
    HELP = "❓"
    LANGUAGE = "🌐"
    CHANNEL = "📢"
    MEDIA = "📎"
    TEXT = "📄"
    PAYMENT = "💳"
    RECEIPT = "🧾"