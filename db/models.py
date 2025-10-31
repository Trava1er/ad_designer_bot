"""
SQLAlchemy database models for AdDesigner Hub bot.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, JSON, 
    ForeignKey, DECIMAL, Enum as SQLEnum, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Dict, Any, Optional
import enum

Base = declarative_base()


class LanguageEnum(enum.Enum):
    """Supported languages."""
    RU = "ru"
    EN = "en"
    ZH_TW = "zh-tw"


class CurrencyEnum(enum.Enum):
    """Supported currencies."""
    RUB = "RUB"
    USD = "USD"
    USDT = "USDT"


class AdStatusEnum(enum.Enum):
    """Advertisement status values."""
    DRAFT = "draft"
    WAITING_PAYMENT = "waiting_payment"
    WAITING_MODERATION = "waiting_moderation"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class PaymentStatusEnum(enum.Enum):
    """Payment status values."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class User(Base):
    """User model for storing Telegram user information."""
    
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(255), nullable=True, index=True)
    full_name = Column(String(255), nullable=False)
    language = Column(SQLEnum(LanguageEnum), default=LanguageEnum.RU)
    created_at = Column(DateTime, default=func.now())
    is_banned = Column(Boolean, default=False)
    
    # Relationships
    ads = relationship("Ad", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    receipts = relationship("Receipt", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, full_name='{self.full_name}')>"


class Channel(Base):
    """Channel model for storing target channels information."""
    
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    telegram_channel_id = Column(BigInteger, nullable=False, unique=True)
    posting_rules = Column(JSON, nullable=True)  # {max_media, allow_video, schedule}
    currency_overrides = Column(JSON, nullable=True)  # {RUB: multiplier, USD: multiplier}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    ads = relationship("Ad", back_populates="channel")
    
    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, title='{self.title}', telegram_id={self.telegram_channel_id})>"


class Tariff(Base):
    """Tariff model for storing pricing plans."""
    
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # "Single", "5 posts", "Subscription 30d"
    posts_limit = Column(Integer, nullable=False)  # Number of posts included
    period_days = Column(Integer, nullable=True)  # Period in days (null for one-time)
    price_rub = Column(DECIMAL(10, 2), nullable=True)
    price_usd = Column(DECIMAL(10, 2), nullable=True)
    price_usdt = Column(DECIMAL(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    ads = relationship("Ad", back_populates="tariff")
    subscriptions = relationship("Subscription", back_populates="subscriptions")
    
    def __repr__(self) -> str:
        return f"<Tariff(id={self.id}, name='{self.name}', posts={self.posts_limit})>"


class Ad(Base):
    """Advertisement model."""
    
    __tablename__ = "ads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=True)
    
    text = Column(Text, nullable=False)
    media = Column(JSON, nullable=True)  # List of file_ids or URLs
    status = Column(SQLEnum(AdStatusEnum), default=AdStatusEnum.DRAFT)
    
    created_at = Column(DateTime, default=func.now())
    published_at = Column(DateTime, nullable=True)
    moderator_id = Column(BigInteger, nullable=True)  # Admin who moderated
    rejection_reason = Column(Text, nullable=True)
    
    # Additional metadata
    generation_data = Column(JSON, nullable=True)  # Store OpenAI generation params
    edit_history = Column(JSON, nullable=True)  # Track edits
    
    # Relationships
    user = relationship("User", back_populates="ads")
    channel = relationship("Channel", back_populates="ads")
    tariff = relationship("Tariff", back_populates="ads")
    payments = relationship("Payment", back_populates="ad")
    receipts = relationship("Receipt", back_populates="ad")
    
    def __repr__(self) -> str:
        return f"<Ad(id={self.id}, user_id={self.user_id}, status='{self.status.value}')>"


class Payment(Base):
    """Payment model for tracking transactions."""
    
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    ad_id = Column(Integer, ForeignKey("ads.id"), nullable=True)
    
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(SQLEnum(CurrencyEnum), nullable=False)
    provider = Column(String(50), nullable=False)  # yookassa, stripe, crypto
    status = Column(SQLEnum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING)
    
    external_id = Column(String(255), nullable=True, index=True)  # Provider payment ID
    txid = Column(String(255), nullable=True)  # Crypto transaction ID
    
    created_at = Column(DateTime, default=func.now())
    paid_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Additional payment data
    payment_data = Column(JSON, nullable=True)  # Store provider-specific data
    webhook_data = Column(JSON, nullable=True)  # Store webhook payload
    
    # Relationships
    user = relationship("User", back_populates="payments")
    ad = relationship("Ad", back_populates="payments")
    receipts = relationship("Receipt", back_populates="payment")
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, currency='{self.currency.value}', status='{self.status.value}')>"


class Subscription(Base):
    """Subscription model for recurring tariffs."""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=False)
    
    started_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    remaining_posts = Column(Integer, nullable=False)
    
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    tariff = relationship("Tariff", back_populates="subscriptions")
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, remaining={self.remaining_posts})>"


class Receipt(Base):
    """Receipt model for storing payment receipts."""
    
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    ad_id = Column(Integer, ForeignKey("ads.id"), nullable=True)
    
    file_path = Column(String(500), nullable=False)  # Path to PDF file
    receipt_number = Column(String(100), nullable=False, unique=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="receipts")
    payment = relationship("Payment", back_populates="receipts")
    ad = relationship("Ad", back_populates="receipts")
    
    def __repr__(self) -> str:
        return f"<Receipt(id={self.id}, receipt_number='{self.receipt_number}')>"


class AdminAction(Base):
    """Admin action log model."""
    
    __tablename__ = "admin_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)  # Admin user ID
    action_type = Column(String(50), nullable=False)  # approve, reject, edit, etc.
    target_type = Column(String(50), nullable=False)  # ad, user, etc.
    target_id = Column(Integer, nullable=False)
    
    details = Column(JSON, nullable=True)  # Action details
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self) -> str:
        return f"<AdminAction(id={self.id}, admin_id={self.admin_id}, action='{self.action_type}')>"


class BotMetrics(Base):
    """Bot metrics model for analytics."""
    
    __tablename__ = "bot_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(500), nullable=False)
    user_id = Column(BigInteger, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self) -> str:
        return f"<BotMetrics(metric='{self.metric_name}', value='{self.metric_value}')>"

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, JSON, 
    ForeignKey, DECIMAL, Enum as SQLEnum, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import List, Dict, Any, Optional
import enum

Base = declarative_base()


class User(Base):
    """User model for storing Telegram user information."""
    
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(255), nullable=True, index=True)
    full_name = Column(String(255), nullable=False)
    language = Column(SQLEnum(LanguageEnum), default=LanguageEnum.RU)
    created_at = Column(DateTime, default=func.now())
    is_banned = Column(Boolean, default=False)
    
    # Relationships
    ads = relationship("Ad", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    receipts = relationship("Receipt", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, full_name='{self.full_name}')>"


class Channel(Base):
    """Channel model for storing target channels information."""
    
    __tablename__ = "channels"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    telegram_channel_id = Column(BigInteger, nullable=False, unique=True)
    posting_rules = Column(JSON, nullable=True)  # {max_media, allow_video, schedule}
    currency_overrides = Column(JSON, nullable=True)  # {RUB: multiplier, USD: multiplier}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    ads = relationship("Ad", back_populates="channel")
    
    def __repr__(self) -> str:
        return f"<Channel(id={self.id}, title='{self.title}', telegram_id={self.telegram_channel_id})>"
    
    @property
    def max_media(self) -> int:
        """Get maximum media files allowed for this channel."""
        if self.posting_rules and "max_media" in self.posting_rules:
            return self.posting_rules["max_media"]
        return 10
    
    @property
    def allow_video(self) -> bool:
        """Check if video is allowed for this channel."""
        if self.posting_rules and "allow_video" in self.posting_rules:
            return self.posting_rules["allow_video"]
        return True


class Tariff(Base):
    """Tariff model for storing pricing plans."""
    
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # "Single", "5 posts", "Subscription 30d"
    posts_limit = Column(Integer, nullable=False)  # Number of posts included
    period_days = Column(Integer, nullable=True)  # Period in days (null for one-time)
    price_rub = Column(DECIMAL(10, 2), nullable=True)
    price_usd = Column(DECIMAL(10, 2), nullable=True)
    price_usdt = Column(DECIMAL(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    ads = relationship("Ad", back_populates="tariff")
    subscriptions = relationship("Subscription", back_populates="tariff")
    
    def __repr__(self) -> str:
        return f"<Tariff(id={self.id}, name='{self.name}', posts={self.posts_limit})>"
    
    def get_price(self, currency: str) -> Optional[float]:
        """Get price for specified currency."""
        if currency == Currency.RUB:
            return float(self.price_rub) if self.price_rub else None
        elif currency == Currency.USD:
            return float(self.price_usd) if self.price_usd else None
        elif currency == Currency.USDT:
            return float(self.price_usdt) if self.price_usdt else None
        return None


class Ad(Base):
    """Advertisement model."""
    
    __tablename__ = "ads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=True)
    
    text = Column(Text, nullable=False)
    media = Column(JSON, nullable=True)  # List of file_ids or URLs
    status = Column(SQLEnum(AdStatus), default=AdStatus.DRAFT)
    
    created_at = Column(DateTime, default=func.now())
    published_at = Column(DateTime, nullable=True)
    moderator_id = Column(BigInteger, nullable=True)  # Admin who moderated
    rejection_reason = Column(Text, nullable=True)
    
    # Additional metadata
    generation_data = Column(JSON, nullable=True)  # Store OpenAI generation params
    edit_history = Column(JSON, nullable=True)  # Track edits
    
    # Relationships
    user = relationship("User", back_populates="ads")
    channel = relationship("Channel", back_populates="ads")
    tariff = relationship("Tariff", back_populates="ads")
    payments = relationship("Payment", back_populates="ad")
    receipts = relationship("Receipt", back_populates="ad")
    
    def __repr__(self) -> str:
        return f"<Ad(id={self.id}, user_id={self.user_id}, status='{self.status}')>"
    
    @property
    def media_count(self) -> int:
        """Get number of media files."""
        return len(self.media) if self.media else 0
    
    @property
    def has_video(self) -> bool:
        """Check if ad contains video."""
        if not self.media:
            return False
        # This would need to be implemented based on how you store media info
        return any("video" in str(media).lower() for media in self.media)


class Payment(Base):
    """Payment model for tracking transactions."""
    
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    ad_id = Column(Integer, ForeignKey("ads.id"), nullable=True)
    
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(SQLEnum(Currency), nullable=False)
    provider = Column(String(50), nullable=False)  # yookassa, stripe, crypto
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    
    external_id = Column(String(255), nullable=True, index=True)  # Provider payment ID
    txid = Column(String(255), nullable=True)  # Crypto transaction ID
    
    created_at = Column(DateTime, default=func.now())
    paid_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Additional payment data
    payment_data = Column(JSON, nullable=True)  # Store provider-specific data
    webhook_data = Column(JSON, nullable=True)  # Store webhook payload
    
    # Relationships
    user = relationship("User", back_populates="payments")
    ad = relationship("Ad", back_populates="payments")
    receipts = relationship("Receipt", back_populates="payment")
    
    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, amount={self.amount}, currency='{self.currency}', status='{self.status}')>"


class Subscription(Base):
    """Subscription model for recurring tariffs."""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"), nullable=False)
    
    started_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    remaining_posts = Column(Integer, nullable=False)
    
    is_active = Column(Boolean, default=True)
    auto_renew = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    tariff = relationship("Tariff", back_populates="subscriptions")
    
    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, remaining={self.remaining_posts})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        return datetime.utcnow() > self.expires_at
    
    @property
    def can_post(self) -> bool:
        """Check if user can create new post with this subscription."""
        return self.is_active and not self.is_expired and self.remaining_posts > 0


class Receipt(Base):
    """Receipt model for storing payment receipts."""
    
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    ad_id = Column(Integer, ForeignKey("ads.id"), nullable=True)
    
    file_path = Column(String(500), nullable=False)  # Path to PDF file
    receipt_number = Column(String(100), nullable=False, unique=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="receipts")
    payment = relationship("Payment", back_populates="receipts")
    ad = relationship("Ad", back_populates="receipts")
    
    def __repr__(self) -> str:
        return f"<Receipt(id={self.id}, receipt_number='{self.receipt_number}')>"


class AdminAction(Base):
    """Admin action log model."""
    
    __tablename__ = "admin_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(BigInteger, nullable=False)  # Admin user ID
    action_type = Column(String(50), nullable=False)  # approve, reject, edit, etc.
    target_type = Column(String(50), nullable=False)  # ad, user, etc.
    target_id = Column(Integer, nullable=False)
    
    details = Column(JSON, nullable=True)  # Action details
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self) -> str:
        return f"<AdminAction(id={self.id}, admin_id={self.admin_id}, action='{self.action_type}')>"


class BotMetrics(Base):
    """Bot metrics model for analytics."""
    
    __tablename__ = "bot_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(String(500), nullable=False)
    user_id = Column(BigInteger, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    def __repr__(self) -> str:
        return f"<BotMetrics(metric='{self.metric_name}', value='{self.metric_value}')>"