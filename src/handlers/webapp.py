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
        plan_id = data.get("plan")  # e.g., "pack10", "week", "month"
        currency = data.get("currency", "rub").upper()  # e.g., "RUB", "USD", "USDT"
        payment_method = data.get("payment_method")  # "card", "crypto", "stars"
        amount = data.get("amount")  # Price from Web App
        
        # Get user info
        user_id, language = await get_user_info_from_message(
            message, 
            get_db_session, 
            get_or_create_user
        )
        
        # Get localized plan and payment method names
        plan_name = MessageLoader.get_message(f"tariff_plans.{plan_id}", language)
        payment_name = MessageLoader.get_message(f"payment_methods.{payment_method}", language)
        
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
            payment_method=payment_method
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
                media=media
            )
            
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
