"""
Utility functions shared across all handlers.
"""

from typing import Optional, Tuple
from sqlalchemy.orm import Session

from database import DatabaseManager, User

from decimal import Decimal


def get_user_language(user: Optional[User]) -> str:
    """Get user language or return default 'ru'."""
    return getattr(user, 'language', 'ru') if user else "ru"


def get_db_session():
    """Get database session context manager."""
    db_manager = DatabaseManager()
    return db_manager.get_session()


def get_user_and_language(db: Session, user_id: int) -> Tuple[Optional[User], str]:
    """Get user from database and their language in one call."""
    user = db.query(User).filter(User.id == user_id).first()
    language = get_user_language(user)
    return user, language


async def get_or_create_user(user_id: int, username: Optional[str] = None, 
                              full_name: Optional[str] = None, 
                              db: Optional[Session] = None) -> User:
    """Get or create user in database."""
    if not db:
        with get_db_session() as db:
            return await get_or_create_user(user_id, username, full_name, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        user = User(
            id=user_id,
            username=username or "unknown",
            full_name=full_name or "Unknown",
            language=None  # Let user choose language on first start
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    return user

def get_price_amount(currency: str, package_type: str) -> Decimal:
    """Get price amount for currency and package."""
    prices = {
        "RUB": {"single": Decimal("150"), "package": Decimal("650")},
        "USD": {"single": Decimal("3"), "package": Decimal("12")},
        "USDT": {"single": Decimal("3"), "package": Decimal("12")}
    }
    return prices.get(currency, {}).get(package_type, Decimal("0"))

def get_price_text(currency: str, package_type: str) -> str:
    """Get price text for currency and package."""
    prices = {
        "RUB": {"single": "150 ₽", "package": "650 ₽"},
        "USD": {"single": "3 USD", "package": "12 USD"},
        "USDT": {"single": "3 USDT", "package": "12 USDT"}
    }
    return prices.get(currency, {}).get(package_type, "Unknown")