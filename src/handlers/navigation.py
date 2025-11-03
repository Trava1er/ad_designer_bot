"""
Navigation handlers for AdDesigner Hub Telegram Bot.
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

from database import AdRepository

from utils import (
    get_main_menu_keyboard, bot_logger,
    get_my_ads_keyboard, get_confirmation_keyboard,
    KeyboardLoader, MessageLoader,
    get_user_info_from_message
)

from .db_helpers import get_db_session, get_user_and_language, get_or_create_user

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.in_(KeyboardLoader.get_button_texts_all_langs("main_menu", (1, 1))))
async def help_command(message: Message):
    """Show help information according to JSON structure."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
        
    # Help text from JSON
    help_text = MessageLoader.get_message("help.text", language)
    
    await message.answer(
        help_text,
        reply_markup=get_confirmation_keyboard(language)
    )
    
    bot_logger.log_user_action(user_id, "help_viewed", "")



@router.message(F.text.in_(KeyboardLoader.get_button_texts_all_langs("main_menu", (1, 0))))
async def my_ads_command(message: Message):
    """Show user's ads with progress bar visualization."""
    from progress_bar import get_progress_bar, get_status_description
    
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
        
    # Get user's ads
    with get_db_session() as db:
        ads = AdRepository.get_user_ads(db, user_id)
    
    if not ads:
        no_ads_text = MessageLoader.get_message("ads.no_ads", language)
        await message.answer(no_ads_text)
        return
    
    # Show ads list title
    ads_text = MessageLoader.get_message("ads.my_ads_title", language)
    
    for ad in ads:
        ad_text = getattr(ad, 'text', '')
        created_at = getattr(ad, 'created_at', None)
        date_str = created_at.strftime('%d.%m.%Y') if created_at else 'N/A'
        ad_status = getattr(ad, 'status', 'draft')
        
        # Get publication details
        channel_id = getattr(ad, 'channel_id', None)
        post_link = getattr(ad, 'post_link', None) or 'N/A'
        amount_paid = getattr(ad, 'amount_paid', None)
        placement_duration = getattr(ad, 'placement_duration', None)
        
        # Format channel display
        if channel_id:
            # Extract username from channel_id or use default
            channel_display = f"@{channel_id.lstrip('@-')}" if channel_id else 'N/A'
        else:
            channel_display = 'N/A'
        
        # Format amount
        amount_display = f"{amount_paid} ₽" if amount_paid else 'N/A'
        
        # Duration display
        duration_display = placement_duration if placement_duration else 'N/A'
        
        # Generate progress bar
        progress_bar = get_progress_bar(ad_status, language)
        status_desc = get_status_description(ad_status, language)
        
        ad_info = MessageLoader.get_message(
            "ads.ad_info",
            language,
            ad_id=getattr(ad, 'id', 0),
            date=date_str,
            status=getattr(ad, 'status', 'unknown'),
            channel=channel_display,
            link=post_link,
            amount=amount_display,
            duration=duration_display,
            text=ad_text[:100] + ('...' if len(ad_text) > 100 else '')
        )
        
        # Add progress bar to ad info
        ad_info_with_progress = f"{ad_info}\n\n📊 <b>Прогресс:</b>\n{progress_bar}\n\n{status_desc}"
        
        await message.answer(
            ad_info_with_progress,
            reply_markup=get_my_ads_keyboard(language),
            parse_mode="HTML"
        )


# ========================= AD TEXT PROCESSING WITH AI =========================



@router.message(F.text.in_(["🏠 Главное меню", "🏠 Main Menu", "🏠 主選單"]))
async def handle_main_menu_button(message: Message, state: FSMContext):
    """Handle main menu button press from any keyboard."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    # Clear any active state
    await state.clear()
    
    welcome_text = MessageLoader.get_message("main_menu", language)
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(language)
    )


@router.message()
async def handle_unknown_message(message: Message):
    """Handle unknown messages."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
        
    unknown_text = MessageLoader.get_message("errors.unknown_command", language)
    
    await message.answer(
        unknown_text,
        reply_markup=get_main_menu_keyboard(language)
    )

