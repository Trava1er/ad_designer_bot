"""
Telegram Web App handler for tariff selection.
"""
import json
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import DatabaseManager, AdRepository
from services import PublicationService
from utils import (
    get_user_info_from_message,
    get_payment_method_keyboard,
    get_main_menu_keyboard,
    UserStates,
    MessageLoader
)
from .db_helpers import get_db_session, get_or_create_user

router = Router(name="webapp")
logger = logging.getLogger(__name__)


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message, state: FSMContext):
    """
    Handle data from Telegram Web App.
    
    Receives tariff selection and payment method from webapp.
    """
    try:
        # Parse data from Web App
        if not message.web_app_data:
            # Get user language first
            user_id, language = await get_user_info_from_message(
                message, 
                get_db_session, 
                get_or_create_user
            )
            error_text = MessageLoader.get_message("webapp_errors.no_data", language)
            await message.answer(error_text)
            return
        
        data = json.loads(message.web_app_data.data)
        
        # New unified order data structure
        plan_id = data.get("tariff")  # "basic", "standard", "premium"
        currency = data.get("currency", "RUB").upper()
        payment_method = data.get("payment")  # "card", "crypto", "stars"
        
        # Additional criteria from unified order page
        placement_type = data.get("placementType")  # "onetime", "subscription"
        publication_time = data.get("publicationTime")  # "immediate", "scheduled"
        scheduled_time = data.get("scheduledTime")  # e.g., "12:00" if scheduled
        pinning = data.get("pinning")  # "yes", "no"
        pin_duration = data.get("pinDuration")  # 1, 3, 7 (days) if pinning is yes
        ad_format = data.get("format")  # "text", "image", "video", "combined"
        duration = data.get("duration", 30)  # 1-90 days
        
        # Validate tariff
        valid_tariffs = ["basic", "standard", "premium"]
        if plan_id not in valid_tariffs:
            logger.warning(f"Invalid tariff received: {plan_id}")
            user_id, language = await get_user_info_from_message(
                message, 
                get_db_session, 
                get_or_create_user
            )
            error_text = MessageLoader.get_message("errors.invalid_tariff", language)
            await message.answer(error_text)
            return
        
        # Validate currency
        valid_currencies = ["RUB", "USD", "CNY"]
        if currency not in valid_currencies:
            logger.warning(f"Invalid currency received: {currency}")
            currency = "RUB"  # Default fallback
        
        # Validate payment method
        valid_payment_methods = ["stars", "card", "crypto"]
        if payment_method not in valid_payment_methods:
            logger.warning(f"Invalid payment method received: {payment_method}")
            user_id, language = await get_user_info_from_message(
                message, 
                get_db_session, 
                get_or_create_user
            )
            error_text = MessageLoader.get_message("errors.invalid_tariff", language)
            await message.answer(error_text)
            return
        
        # Calculate amount from tariff prices (should match pricing_config.json)
        tariff_prices = {
            "basic": {"RUB": 500, "USD": 6, "CNY": 40},
            "standard": {"RUB": 1200, "USD": 14, "CNY": 95},
            "premium": {"RUB": 2500, "USD": 30, "CNY": 200}
        }
        amount = tariff_prices.get(plan_id, {}).get(currency, 0)
        
        if amount == 0:
            logger.error(f"Invalid amount calculated for tariff {plan_id} and currency {currency}")
            user_id, language = await get_user_info_from_message(
                message, 
                get_db_session, 
                get_or_create_user
            )
            error_text = MessageLoader.get_message("errors.invalid_tariff", language)
            await message.answer(error_text)
            return
        
        # Get user info
        user_id, language = await get_user_info_from_message(
            message, 
            get_db_session, 
            get_or_create_user
        )
        
        # Get localized tariff name
        tariff_names = {
            "ru": {"basic": "Базовый", "standard": "Стандарт", "premium": "Премиум"},
            "en": {"basic": "Basic", "standard": "Standard", "premium": "Premium"},
            "zh-tw": {"basic": "基本", "standard": "標準", "premium": "高級"}
        }
        plan_name = tariff_names.get(language, tariff_names["ru"]).get(plan_id, plan_id)
        
        # Get localized payment method name
        payment_names = {
            "ru": {"stars": "Telegram Stars", "card": "Банковская карта", "crypto": "Криптовалюта"},
            "en": {"stars": "Telegram Stars", "card": "Bank Card", "crypto": "Cryptocurrency"},
            "zh-tw": {"stars": "Telegram Stars", "card": "銀行卡", "crypto": "加密貨幣"}
        }
        payment_name = payment_names.get(language, payment_names["ru"]).get(payment_method, payment_method)
        
        # Validate
        if not plan_id or not payment_method or not amount:
            error_text = MessageLoader.get_message("errors.invalid_tariff", language)
            await message.answer(error_text)
            return
        
        # Save to state
        await state.update_data(
            selected_plan=plan_id,
            selected_plan_name=plan_name,
            currency=currency,
            amount=amount,
            payment_method=payment_method,
            # New placement criteria
            placement_type=placement_type,
            publication_time=publication_time,
            scheduled_time=scheduled_time,
            pinning=pinning,
            pin_duration=pin_duration,
            ad_format=ad_format,
            duration=duration
        )
        
        # Get ad text from state
        state_data = await state.get_data()
        ad_text = state_data.get("ad_text", "")
        image_file_id = state_data.get("image_file_id")
        has_image = state_data.get("has_image", False)
        
        if not ad_text:
            error_text = MessageLoader.get_message("errors.general", language)
            await message.answer(error_text)
            return
        
        # Create ad in database
        with get_db_session() as db:
            ad = AdRepository.create_ad(
                db=db,
                user_id=user_id,
                text=ad_text,
                media=image_file_id if has_image and image_file_id else None
            )
            ad_id = ad.id
            db.commit()
        
        # Publish ad to channel
        try:
            media = [image_file_id] if has_image and image_file_id else None
            channel_username, channel_id, message_id = await PublicationService.publish_ad(
                ad_id=ad_id,
                text=ad_text,
                media=media,
                language=language
            )
            
            logger.info(f"[DEBUG] Published ad - username: {channel_username}, channel_id: {channel_id}, message_id: {message_id}")
            
            # Update ad with publication details
            with get_db_session() as db:
                updated_ad = AdRepository.update_ad_status(
                    db=db,
                    ad_id=ad_id,
                    status="published"
                )
                if updated_ad:
                    # Update additional fields
                    updated_ad.channel_id = f"@{channel_username}" if channel_username else str(channel_id)
                    updated_ad.amount_paid = float(amount)
                    updated_ad.placement_duration = plan_name
                    db.commit()
            
            # Create post link
            if channel_username:
                post_link = f"https://t.me/{channel_username}/{message_id}"
            else:
                # If no username, use channel ID format (remove -100 prefix)
                clean_channel_id = str(channel_id).replace('-100', '')
                post_link = f"https://t.me/c/{clean_channel_id}/{message_id}"
            
            # Отправляем успешное сообщение с деталями
            success_message = MessageLoader.get_message(
                "payment.success_published",
                language,
                plan=plan_name,
                amount=amount,
                currency=currency,
                payment=payment_name,
                text=ad_text,
                link=post_link
            )
            
            await message.answer(
                success_message,
                parse_mode="HTML",
                reply_markup=get_main_menu_keyboard(language)
            )
            
        except Exception as e:
            logger.error(f"Error publishing ad: {e}", exc_info=True)
            # Ad created but not published
            error_text = MessageLoader.get_message("errors.general", language)
            await message.answer(error_text)
            return
        
        # Clear state
        await state.clear()
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        error_text = MessageLoader.get_message("errors.general", language)
        await message.answer(error_text)
    except Exception as e:
        logger.error(f"Error handling webapp data: {e}", exc_info=True)
        error_text = MessageLoader.get_message("errors.general", language)
        await message.answer(error_text)
