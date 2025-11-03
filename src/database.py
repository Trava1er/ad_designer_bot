"""
Unified database module for AdDesigner Hub Telegram Bot.
Contains models, session management, and repository functions.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from decimal import Decimal

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Boolean, 
    Text, DECIMAL, ForeignKey, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.engine import Engine
from contextlib import contextmanager

from bot_config import settings

logger = logging.getLogger(__name__)

# Database base
Base = declarative_base()


# ========================= ENUMS =========================

class LanguageEnum(Enum):
    """Language enumeration."""
    RU = "ru"
    EN = "en"
    ZH_TW = "zh-tw"


class AdStatusEnum(Enum):
    """Ad status enumeration."""
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"


class PaymentStatusEnum(Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CurrencyEnum(Enum):
    """Currency enumeration."""
    RUB = "RUB"
    USD = "USD"
    USDT = "USDT"


# ========================= MODELS =========================

class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)  # Telegram user ID
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=False)
    language = Column(String(10), default="ru")
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    ads = relationship("Ad", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Ad(Base):
    """Advertisement model."""
    __tablename__ = "ads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    media = Column(Text, nullable=True)  # JSON string with media files
    status = Column(String(20), default="draft")
    moderator_id = Column(Integer, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Publication details
    channel_id = Column(String(255), nullable=True)  # Telegram channel ID
    post_link = Column(Text, nullable=True)  # Link to published post
    amount_paid = Column(DECIMAL(10, 2), nullable=True)  # Amount paid for this ad
    placement_duration = Column(String(100), nullable=True)  # e.g., "30 дней", "permanent"
    
    # Relationships
    user = relationship("User", back_populates="ads")


class Payment(Base):
    """Payment model."""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ad_id = Column(Integer, ForeignKey("ads.id"), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    status = Column(String(20), default="pending")
    provider = Column(String(50), nullable=False)
    external_id = Column(String(255), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="payments")


class Tariff(Base):
    """Tariff model."""
    __tablename__ = "tariffs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)  # Added description field
    posts_limit = Column(Integer, nullable=False)
    period_days = Column(Integer, nullable=True)  # None for one-time
    price_rub = Column(DECIMAL(10, 2), nullable=True)
    price_usd = Column(DECIMAL(10, 2), nullable=True)
    price_usdt = Column(DECIMAL(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


# ========================= DATABASE ENGINE =========================

# SQLite configuration
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragma for better performance."""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


class DatabaseManager:
    """Database connection and session manager (Singleton)."""
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._engine is None:
            self._init_engine()
    
    def _init_engine(self):
        """Initialize database engine and session factory."""
        try:
            # Use connection pooling for better performance
            self._engine = create_engine(
                settings.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self._session_factory = sessionmaker(bind=self._engine)
            logger.info(f"Database engine configured for: {settings.database_url}")
            
        except Exception as e:
            logger.error(f"Database configuration error: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup."""
        if self._session_factory is None:
            self._init_engine()
        
        if self._session_factory is None:
            raise RuntimeError("Failed to initialize database session factory")
            
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def init_db(self):
        """Initialize database tables."""
        try:
            if self._engine is None:
                self._init_engine()
            
            Base.metadata.create_all(self._engine)
            logger.info("Database tables created successfully")
            
            # Create default data
            with self.get_session() as session:
                self._create_default_data(session)
            
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _create_default_data(self, session):
        """Create default data if not exists."""
        try:
            # Check if tariffs already exist
            if session.query(Tariff).count() == 0:
                tariffs = [
                    Tariff(
                        name="Базовый",
                        description="3 публикации в неделю",
                        posts_limit=3,
                        period_days=7,
                        price_rub=500,
                        price_usd=5,
                        price_usdt=5
                    ),
                    Tariff(
                        name="Стандарт",
                        description="10 публикаций в неделю + AI улучшения",
                        posts_limit=10,
                        period_days=7,
                        price_rub=1500,
                        price_usd=15,
                        price_usdt=15
                    ),
                    Tariff(
                        name="Премиум",
                        description="Безлимитные публикации + все возможности",
                        posts_limit=999,  # Unlimited
                        period_days=30,
                        price_rub=3000,
                        price_usd=30,
                        price_usdt=30
                    )
                ]
                for tariff in tariffs:
                    session.add(tariff)
                session.commit()
                logger.info("Default tariffs created")
        except Exception as e:
            logger.error(f"Error creating default data: {e}")
            session.rollback()


# ========================= REPOSITORY FUNCTIONS =========================

class UserRepository:
    """User repository functions."""
    
    @staticmethod
    def get_or_create(db: Session, user_id: int, username: str = "", full_name: str = "") -> User:
        """Get or create user."""
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            user = User(
                id=user_id,
                username=username or "unknown",
                full_name=full_name or "Unknown",
                language="ru"
            )
            db.add(user)
            db.flush()
            
        return user
    
    @staticmethod
    def update_language(db: Session, user_id: int, language: str):
        """Update user language."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            setattr(user, 'language', language)
            db.flush()
        return user
    
    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        """Get all users."""
        return db.query(User).filter(User.is_active == True).all()


class AdRepository:
    """Ad repository functions."""
    
    @staticmethod
    def create_ad(db: Session, user_id: int, text: str, media: Optional[str] = None) -> Ad:
        """Create new ad."""
        ad = Ad(
            user_id=user_id,
            text=text,
            media=media,
            status="draft"
        )
        db.add(ad)
        db.flush()
        return ad
    
    @staticmethod
    def get_pending_ads(db: Session) -> List[Ad]:
        """Get pending ads for moderation."""
        return db.query(Ad).filter(Ad.status == "pending").all()
    
    @staticmethod
    def get_user_ads(db: Session, user_id: int) -> List[Ad]:
        """Get user's ads."""
        return db.query(Ad).filter(Ad.user_id == user_id).all()
    
    @staticmethod
    def update_ad_status(db: Session, ad_id: int, status: str, moderator_id: Optional[int] = None, reason: Optional[str] = None) -> Optional[Ad]:
        """Update ad status."""
        ad = db.query(Ad).filter(Ad.id == ad_id).first()
        if ad:
            setattr(ad, 'status', status)
            if moderator_id is not None:
                setattr(ad, 'moderator_id', moderator_id)
            if reason is not None:
                setattr(ad, 'rejection_reason', reason)
            if status == "published":
                setattr(ad, 'published_at', datetime.now())
            db.flush()
        return ad


class PaymentRepository:
    """Payment repository functions."""
    
    @staticmethod
    def create_payment(db: Session, user_id: int, amount: Decimal, currency: str, provider: str, ad_id: Optional[int] = None) -> Payment:
        """Create new payment."""
        payment = Payment(
            user_id=user_id,
            ad_id=ad_id,
            amount=amount,
            currency=currency,
            provider=provider,
            status="pending"
        )
        db.add(payment)
        db.flush()
        return payment
    
    @staticmethod
    def update_payment_status(db: Session, payment_id: int, status: str, external_id: Optional[str] = None) -> Optional[Payment]:
        """Update payment status."""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            setattr(payment, 'status', status)
            if external_id:
                setattr(payment, 'external_id', external_id)
            if status == "paid":
                setattr(payment, 'paid_at', datetime.now())
            db.flush()
        return payment
    
    @staticmethod
    def get_user_payments(db: Session, user_id: int) -> List[Payment]:
        """Get user's payments."""
        return db.query(Payment).filter(Payment.user_id == user_id).all()


class TariffRepository:
    """Tariff repository functions."""
    
    @staticmethod
    def get_active_tariffs(db: Session) -> List[Tariff]:
        """Get active tariffs."""
        return db.query(Tariff).filter(Tariff.is_active == True).all()
    
    @staticmethod
    def get_by_id(db: Session, tariff_id: int) -> Optional[Tariff]:
        """Get tariff by ID."""
        return db.query(Tariff).filter(Tariff.id == tariff_id).first()


# ========================= CONVENIENCE FUNCTIONS =========================

# Global database manager instance
db_manager = DatabaseManager()

def init_db():
    """Initialize database."""
    db_manager.init_db()

def get_db_session():
    """Get database session."""
    return db_manager.get_session()

# Legacy compatibility
def init_database():
    """Legacy function name."""
    return init_db()