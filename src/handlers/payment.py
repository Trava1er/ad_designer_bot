"""
Payment handlers for AdDesigner Hub Telegram Bot.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from database import (
    DatabaseManager, User, Ad, Payment,
    LanguageEnum, AdStatusEnum, PaymentStatusEnum, CurrencyEnum,
    UserRepository, AdRepository, PaymentRepository, TariffRepository
)
from utils import (
    PaymentStates, UserStates, MessageLoader, KeyboardLoader,
    get_main_menu_keyboard, bot_logger,
    get_tariff_selection_keyboard, get_payment_method_keyboard,
    proceed_to_tariff_selection,
    get_user_info_from_message, handle_tariff_selection
)
from .db_helpers import (
    get_db_session, get_user_and_language, 
    get_or_create_user, get_price_amount,
    get_price_text
)

logger = logging.getLogger(__name__)
router = Router()


# ========================= ADMIN HANDLERS =========================



@router.message(PaymentStates.selecting_currency)
async def process_package_selection(message: Message, state: FSMContext):
    """Process package selection."""
    if message.text not in ["1", "5"]:
        await message.answer(MessageLoader.get_message("payment.invalid_package"))
        return
    
    data = await state.get_data()
    currency = data.get("selected_currency")
    if not currency:
        await message.answer(MessageLoader.get_message("payment.currency_not_selected"))
        return
        
    package_type = "single" if message.text == "1" else "package"
    
    amount = get_price_amount(currency, package_type)
    
    # Create payment in database
    db_manager = DatabaseManager()
        # Check if message has from_user
    if not message.from_user:
        await message.answer(MessageLoader.get_message("payment.user_info_unavailable"))
        return
        
    with db_manager.get_session() as db:
        payment = Payment(
            user_id=message.from_user.id,
            amount=amount,
            currency=CurrencyEnum(currency),
            provider=get_provider_name(currency),
            status=PaymentStatusEnum.PENDING
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # Get user language for keyboard and messages
        user, language = get_user_and_language(db, message.from_user.id)
        
        # Demo payment interface
        payment_text = MessageLoader.get_message(
            "payment.demo_payment",
            language,
            package=message.text,
            amount=get_price_text(currency, package_type)
        )
        
        from utils import KeyboardLoader
        keyboard = KeyboardLoader.get_keyboard("payment_processing", language)
        
        await message.answer(
            payment_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await state.set_state(PaymentStates.payment_processing)
        await state.update_data(payment_id=payment.id)
        
        if message.from_user:
            bot_logger.log_user_action(message.from_user.id, "payment_created", str(payment.id))


def get_provider_name(currency: str) -> str:
    """Get provider name for currency."""
    providers = {
        "RUB": "yookassa",
        "USD": "stripe", 
        "USDT": "nowpayments"
    }
    return providers.get(currency, "demo")




@router.message(F.text.in_(KeyboardLoader.get_button_texts_all_langs("payment_processing", (0, 0))))
async def process_payment_success(message: Message, state: FSMContext):
    """Process successful payment."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    # Get payment_id from state
    data = await state.get_data()
    payment_id = data.get("payment_id")
    
    if not payment_id:
        await message.answer(MessageLoader.get_message("payment.info_not_found"))
        return
    
    with get_db_session() as db:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if payment:
            setattr(payment, 'status', PaymentStatusEnum.PAID.value)
            setattr(payment, 'paid_at', datetime.now())
            db.commit()
            
            success_text = MessageLoader.get_message("payment.success", language)
            
            await message.answer(
                success_text,
                reply_markup=get_main_menu_keyboard(language)
            )
            
            await state.clear()
            if message.from_user:
                bot_logger.log_user_action(message.from_user.id, "payment_completed", str(payment.id))




@router.message(F.text.in_(KeyboardLoader.get_button_texts_all_langs("payment_processing", (1, 0))))
async def cancel_payment(message: Message, state: FSMContext):
    """Cancel payment process."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    cancel_text = MessageLoader.get_message("payment.cancelled", language)
    
    await message.answer(
        cancel_text,
        reply_markup=get_main_menu_keyboard(language)
    )
    
    await state.clear()


# ========================= PAYMENT METHOD HANDLERS =========================


@router.message(PaymentStates.payment_method_selection, F.text.in_(KeyboardLoader.get_button_texts_all_langs("payment_method", (0, 0))))
async def handle_payment_card(message: Message, state: FSMContext):
    """Handle bank card payment method selection."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    # Get selected tariff from state
    data = await state.get_data()
    plan_name = data.get("selected_plan")
    
    if not plan_name:
        await message.answer(
            MessageLoader.get_message("payment.no_plan_selected", language) or "Сначала выберите тариф",
            reply_markup=get_tariff_selection_keyboard(language)
        )
        return
    
    # Show payment processing message
    payment_text = MessageLoader.get_message("payment.card_processing", language) or "💳 Обработка платежа картой..."
    await message.answer(
        payment_text,
        reply_markup=KeyboardLoader.get_keyboard("payment_processing", language)
    )
    await state.set_state(PaymentStates.payment_processing)


@router.message(PaymentStates.payment_method_selection, F.text.in_(KeyboardLoader.get_button_texts_all_langs("payment_method", (1, 0))))
async def handle_payment_crypto(message: Message, state: FSMContext):
    """Handle cryptocurrency payment method selection."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    # Get selected tariff from state
    data = await state.get_data()
    plan_name = data.get("selected_plan")
    
    if not plan_name:
        await message.answer(
            MessageLoader.get_message("payment.no_plan_selected", language) or "Сначала выберите тариф",
            reply_markup=get_tariff_selection_keyboard(language)
        )
        return
    
    # Show payment processing message
    payment_text = MessageLoader.get_message("payment.crypto_processing", language) or "💎 Обработка криптоплатежа..."
    await message.answer(
        payment_text,
        reply_markup=KeyboardLoader.get_keyboard("payment_processing", language)
    )
    await state.set_state(PaymentStates.payment_processing)


@router.message(PaymentStates.payment_method_selection, F.text.in_(KeyboardLoader.get_button_texts_all_langs("payment_method", (2, 0))))
async def handle_payment_stars(message: Message, state: FSMContext):
    """Handle Telegram Stars payment method selection."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    # Get selected tariff from state
    data = await state.get_data()
    plan_name = data.get("selected_plan")
    
    if not plan_name:
        await message.answer(
            MessageLoader.get_message("payment.no_plan_selected", language) or "Сначала выберите тариф",
            reply_markup=get_tariff_selection_keyboard(language)
        )
        return
    
    # Show payment processing message
    payment_text = MessageLoader.get_message("payment.stars_processing", language) or "⭐ Обработка оплаты через Telegram Stars..."
    await message.answer(
        payment_text,
        reply_markup=KeyboardLoader.get_keyboard("payment_processing", language)
    )
    await state.set_state(PaymentStates.payment_processing)


# ========================= HELP & OTHER HANDLERS =========================


# Currency selection handler
@router.message(UserStates.currency_selection, F.text.in_(KeyboardLoader.get_button_texts_all_langs("currency_selection", (0, 0))))
async def handle_currency_rub(message: Message, state: FSMContext):
    """Handle RUB currency selection."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    await state.update_data(selected_currency="RUB")
    await proceed_to_tariff_selection(message, language, "RUB", state)


@router.message(UserStates.currency_selection, F.text.in_(KeyboardLoader.get_button_texts_all_langs("currency_selection", (1, 0))))
async def handle_currency_usd(message: Message, state: FSMContext):
    """Handle USD currency selection."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    await state.update_data(selected_currency="USD")
    await proceed_to_tariff_selection(message, language, "USD", state)


@router.message(UserStates.currency_selection, F.text.in_(KeyboardLoader.get_button_texts_all_langs("currency_selection", (2, 0))))
async def handle_currency_usdt(message: Message, state: FSMContext):
    """Handle USDT currency selection."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    await state.update_data(selected_currency="USDT")
    await proceed_to_tariff_selection(message, language, "USDT", state)


# Tariff selection handlers (now receive currency from state)


@router.message(F.text.regexp(r"🎯.*1.*объявление|🎯.*1.*Ad|🎯.*單次"))
async def handle_plan_single(message: Message, state: FSMContext):
    """Handle single ad plan selection."""
    await handle_tariff_selection(
        message, state,
        plan_name="single",
        plan_details={"name": "single", "price": 200, "period_days": None, "ads_count": 1},
        get_user_func=get_user_and_language,
        get_db_func=get_db_session,
        payment_keyboard_func=get_payment_method_keyboard
    )


@router.message(F.text.regexp(r"📦.*10.*объявлен|📦.*10.*Ads|📦.*10次"))
async def handle_plan_month(message: Message, state: FSMContext):
    """Handle monthly plan selection."""
    await handle_tariff_selection(
        message, state,
        plan_name="month",
        plan_details={"name": "month", "price": 800, "period_days": 30, "ads_count": 10},
        get_user_func=get_user_and_language,
        get_db_func=get_db_session,
        payment_keyboard_func=get_payment_method_keyboard
    )


@router.message(F.text.regexp(r"🏆.*Безлимит|🏆.*Unlimited|🏆.*無限"))
async def handle_plan_premium(message: Message, state: FSMContext):
    """Handle premium plan selection."""
    await handle_tariff_selection(
        message, state,
        plan_name="premium",
        plan_details={"name": "premium", "price": 1500, "period_days": 30, "ads_count": 50},
        get_user_func=get_user_and_language,
        get_db_func=get_db_session,
        payment_keyboard_func=get_payment_method_keyboard
    )



