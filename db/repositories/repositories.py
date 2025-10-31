"""
Specific repository classes for each model.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime, timedelta

from db.models import (
    User, Ad, Payment, Tariff, Subscription, Channel, Receipt, 
    AdminAction, BotMetrics, LanguageEnum, CurrencyEnum, 
    AdStatusEnum, PaymentStatusEnum
)


class UserRepository:
    """Repository for User model."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_user(self, user_id: int, username: str, full_name: str, language: LanguageEnum = LanguageEnum.RU) -> User:
        """Create a new user."""
        user = User(
            id=user_id,
            username=username,
            full_name=full_name,
            language=language
        )
        self.session.add(user)
        self.session.flush()
        return user
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        return self.session.query(User).filter(User.id == user_id).first()
    
    def get_or_create(self, user_id: int, username: str, full_name: str, language: LanguageEnum = LanguageEnum.RU) -> tuple[User, bool]:
        """Get existing user or create new one."""
        user = self.get_by_id(user_id)
        if user:
            # Update user info
            user.username = username
            user.full_name = full_name
            return user, False
        
        user = self.create_user(user_id, username, full_name, language)
        return user, True
    
    def update_language(self, user_id: int, language: LanguageEnum) -> Optional[User]:
        """Update user language."""
        user = self.get_by_id(user_id)
        if user:
            user.language = language
            self.session.flush()
        return user
    
    def ban_user(self, user_id: int) -> bool:
        """Ban user."""
        user = self.get_by_id(user_id)
        if user:
            user.is_banned = True
            self.session.flush()
            return True
        return False
    
    def unban_user(self, user_id: int) -> bool:
        """Unban user."""
        user = self.get_by_id(user_id)
        if user:
            user.is_banned = False
            self.session.flush()
            return True
        return False


class ChannelRepository:
    """Repository for Channel model."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_channel(self, title: str, telegram_channel_id: int, posting_rules: Dict = None, currency_overrides: Dict = None) -> Channel:
        """Create a new channel."""
        channel = Channel(
            title=title,
            telegram_channel_id=telegram_channel_id,
            posting_rules=posting_rules,
            currency_overrides=currency_overrides
        )
        self.session.add(channel)
        self.session.flush()
        return channel
    
    def get_by_id(self, channel_id: int) -> Optional[Channel]:
        """Get channel by ID."""
        return self.session.query(Channel).filter(Channel.id == channel_id).first()
    
    def get_by_telegram_id(self, telegram_channel_id: int) -> Optional[Channel]:
        """Get channel by Telegram channel ID."""
        return self.session.query(Channel).filter(Channel.telegram_channel_id == telegram_channel_id).first()
    
    def get_active_channels(self) -> List[Channel]:
        """Get all active channels."""
        return self.session.query(Channel).filter(Channel.is_active == True).all()
    
    def deactivate_channel(self, channel_id: int) -> bool:
        """Deactivate channel."""
        channel = self.get_by_id(channel_id)
        if channel:
            channel.is_active = False
            self.session.flush()
            return True
        return False


class TariffRepository:
    """Repository for Tariff model."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_tariff(self, name: str, posts_limit: int, period_days: int = None, 
                     price_rub: float = None, price_usd: float = None, price_usdt: float = None) -> Tariff:
        """Create a new tariff."""
        tariff = Tariff(
            name=name,
            posts_limit=posts_limit,
            period_days=period_days,
            price_rub=price_rub,
            price_usd=price_usd,
            price_usdt=price_usdt
        )
        self.session.add(tariff)
        self.session.flush()
        return tariff
    
    def get_by_id(self, tariff_id: int) -> Optional[Tariff]:
        """Get tariff by ID."""
        return self.session.query(Tariff).filter(Tariff.id == tariff_id).first()
    
    def get_active_tariffs(self) -> List[Tariff]:
        """Get all active tariffs."""
        return self.session.query(Tariff).filter(Tariff.is_active == True).all()
    
    def deactivate_tariff(self, tariff_id: int) -> bool:
        """Deactivate tariff."""
        tariff = self.get_by_id(tariff_id)
        if tariff:
            tariff.is_active = False
            self.session.flush()
            return True
        return False


class AdRepository:
    """Repository for Ad model."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_ad(self, user_id: int, channel_id: int, text: str, media: List = None, 
                  tariff_id: int = None, generation_data: Dict = None) -> Ad:
        """Create a new ad."""
        ad = Ad(
            user_id=user_id,
            channel_id=channel_id,
            text=text,
            media=media or [],
            tariff_id=tariff_id,
            generation_data=generation_data
        )
        self.session.add(ad)
        self.session.flush()
        return ad
    
    def get_by_id(self, ad_id: int) -> Optional[Ad]:
        """Get ad by ID."""
        return self.session.query(Ad).filter(Ad.id == ad_id).first()
    
    def get_user_ads(self, user_id: int, status: AdStatusEnum = None, limit: int = None) -> List[Ad]:
        """Get ads by user."""
        query = self.session.query(Ad).filter(Ad.user_id == user_id)
        
        if status:
            query = query.filter(Ad.status == status)
        
        query = query.order_by(desc(Ad.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_ads_by_status(self, status: AdStatusEnum, limit: int = None) -> List[Ad]:
        """Get ads by status."""
        query = self.session.query(Ad).filter(Ad.status == status)
        query = query.order_by(desc(Ad.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update_status(self, ad_id: int, status: AdStatusEnum, moderator_id: int = None, rejection_reason: str = None) -> Optional[Ad]:
        """Update ad status."""
        ad = self.get_by_id(ad_id)
        if ad:
            ad.status = status
            if moderator_id:
                ad.moderator_id = moderator_id
            if rejection_reason:
                ad.rejection_reason = rejection_reason
            if status == AdStatusEnum.PUBLISHED:
                ad.published_at = datetime.utcnow()
            self.session.flush()
        return ad
    
    def update_text(self, ad_id: int, text: str) -> Optional[Ad]:
        """Update ad text."""
        ad = self.get_by_id(ad_id)
        if ad:
            ad.text = text
            self.session.flush()
        return ad
    
    def update_media(self, ad_id: int, media: List) -> Optional[Ad]:
        """Update ad media."""
        ad = self.get_by_id(ad_id)
        if ad:
            ad.media = media
            self.session.flush()
        return ad


class PaymentRepository:
    """Repository for Payment model."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_payment(self, user_id: int, amount: float, currency: CurrencyEnum, 
                      provider: str, ad_id: int = None, external_id: str = None) -> Payment:
        """Create a new payment."""
        payment = Payment(
            user_id=user_id,
            ad_id=ad_id,
            amount=amount,
            currency=currency,
            provider=provider,
            external_id=external_id
        )
        self.session.add(payment)
        self.session.flush()
        return payment
    
    def get_by_id(self, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        return self.session.query(Payment).filter(Payment.id == payment_id).first()
    
    def get_by_external_id(self, external_id: str) -> Optional[Payment]:
        """Get payment by external ID."""
        return self.session.query(Payment).filter(Payment.external_id == external_id).first()
    
    def get_user_payments(self, user_id: int, status: PaymentStatusEnum = None) -> List[Payment]:
        """Get payments by user."""
        query = self.session.query(Payment).filter(Payment.user_id == user_id)
        
        if status:
            query = query.filter(Payment.status == status)
        
        return query.order_by(desc(Payment.created_at)).all()
    
    def update_status(self, payment_id: int, status: PaymentStatusEnum, txid: str = None, webhook_data: Dict = None) -> Optional[Payment]:
        """Update payment status."""
        payment = self.get_by_id(payment_id)
        if payment:
            payment.status = status
            if txid:
                payment.txid = txid
            if webhook_data:
                payment.webhook_data = webhook_data
            if status == PaymentStatusEnum.PAID:
                payment.paid_at = datetime.utcnow()
            self.session.flush()
        return payment


class SubscriptionRepository:
    """Repository for Subscription model."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_subscription(self, user_id: int, tariff_id: int, expires_at: datetime, remaining_posts: int) -> Subscription:
        """Create a new subscription."""
        subscription = Subscription(
            user_id=user_id,
            tariff_id=tariff_id,
            expires_at=expires_at,
            remaining_posts=remaining_posts
        )
        self.session.add(subscription)
        self.session.flush()
        return subscription
    
    def get_by_id(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID."""
        return self.session.query(Subscription).filter(Subscription.id == subscription_id).first()
    
    def get_user_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's active subscription."""
        return self.session.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.is_active == True,
                Subscription.expires_at > datetime.utcnow()
            )
        ).first()
    
    def use_post(self, subscription_id: int) -> Optional[Subscription]:
        """Use one post from subscription."""
        subscription = self.get_by_id(subscription_id)
        if subscription and subscription.remaining_posts > 0:
            subscription.remaining_posts -= 1
            self.session.flush()
        return subscription
    
    def deactivate_subscription(self, subscription_id: int) -> bool:
        """Deactivate subscription."""
        subscription = self.get_by_id(subscription_id)
        if subscription:
            subscription.is_active = False
            self.session.flush()
            return True
        return False


class ReceiptRepository:
    """Repository for Receipt model."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_receipt(self, user_id: int, payment_id: int, ad_id: int, file_path: str, receipt_number: str) -> Receipt:
        """Create a new receipt."""
        receipt = Receipt(
            user_id=user_id,
            payment_id=payment_id,
            ad_id=ad_id,
            file_path=file_path,
            receipt_number=receipt_number
        )
        self.session.add(receipt)
        self.session.flush()
        return receipt
    
    def get_by_id(self, receipt_id: int) -> Optional[Receipt]:
        """Get receipt by ID."""
        return self.session.query(Receipt).filter(Receipt.id == receipt_id).first()
    
    def get_by_payment_id(self, payment_id: int) -> Optional[Receipt]:
        """Get receipt by payment ID."""
        return self.session.query(Receipt).filter(Receipt.payment_id == payment_id).first()


class AdminActionRepository:
    """Repository for AdminAction model."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def log_action(self, admin_id: int, action_type: str, target_type: str, target_id: int, details: Dict = None) -> AdminAction:
        """Log admin action."""
        action = AdminAction(
            admin_id=admin_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
        self.session.add(action)
        self.session.flush()
        return action
    
    def get_actions(self, admin_id: int = None, limit: int = 100) -> List[AdminAction]:
        """Get admin actions."""
        query = self.session.query(AdminAction)
        
        if admin_id:
            query = query.filter(AdminAction.admin_id == admin_id)
        
        return query.order_by(desc(AdminAction.created_at)).limit(limit).all()


class RepositoryManager:
    """Manager for all repositories."""
    
    def __init__(self, session: Session):
        self.session = session
        self.users = UserRepository(session)
        self.channels = ChannelRepository(session)
        self.tariffs = TariffRepository(session)
        self.ads = AdRepository(session)
        self.payments = PaymentRepository(session)
        self.subscriptions = SubscriptionRepository(session)
        self.receipts = ReceiptRepository(session)
        self.admin_actions = AdminActionRepository(session)
    
    def commit(self):
        """Commit all changes."""
        self.session.commit()
    
    def rollback(self):
        """Rollback all changes."""
        self.session.rollback()
    
    def close(self):
        """Close session."""
        self.session.close()