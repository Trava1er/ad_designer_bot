"""
Telegram Web App handler for tariff selection.
"""
import json
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database import DatabaseManager
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
            await message.answer("❌ Данные не получены")
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
        
        # Plan names for localization
        plan_names = {
            "pack1": {"ru": "1 объявление", "en": "1 ad", "zh-tw": "1個廣告"},
            "pack5": {"ru": "5 объявлений", "en": "5 ads", "zh-tw": "5個廣告"},
            "pack10": {"ru": "10 объявлений", "en": "10 ads", "zh-tw": "10個廣告"},
            "pack20": {"ru": "20 объявлений", "en": "20 ads", "zh-tw": "20個廣告"},
            "pack30": {"ru": "30 объявлений", "en": "30 ads", "zh-tw": "30個廣告"},
            "week": {"ru": "Безлимит/неделя", "en": "Unlimited/week", "zh-tw": "無限/週"},
            "month": {"ru": "Безлимит/месяц", "en": "Unlimited/month", "zh-tw": "無限/月"},
            "quarter": {"ru": "Безлимит/3 месяца", "en": "Unlimited/3 months", "zh-tw": "無限/3個月"}
        }
        
        payment_method_names = {
            "card": {"ru": "Банковская карта", "en": "Bank card", "zh-tw": "銀行卡"},
            "crypto": {"ru": "Криптовалюта", "en": "Cryptocurrency", "zh-tw": "加密貨幣"},
            "stars": {"ru": "Telegram Stars", "en": "Telegram Stars", "zh-tw": "Telegram Stars"}
        }
        
        # Validate
        if not plan_id or not payment_method or not amount:
            error_text = MessageLoader.get_message("errors.invalid_tariff", language)
            await message.answer(error_text)
            return
        
        plan_name = plan_names.get(plan_id, {}).get(language, plan_id)
        payment_name = payment_method_names.get(payment_method, {}).get(language, payment_method)
        
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
        
        # Create payment and process
        # For now, simulate successful payment and show success message
        success_text = f"""
✅ <b>Платеж успешно обработан!</b>

📦 Тариф: {plan_name}
💰 Сумма: {amount} {currency}
💳 Способ: {payment_name}

📝 Ваше объявление:
<blockquote>{ad_text[:200]}{'...' if len(ad_text) > 200 else ''}</blockquote>

📢 Объявление опубликовано!

🔗 Ссылка на пост: https://t.me/your_channel/123

Спасибо за использование нашего сервиса! 🎉
"""
        
        await message.answer(
            success_text,
            parse_mode="HTML",
            reply_markup=get_main_menu_keyboard(language)
        )
        
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
