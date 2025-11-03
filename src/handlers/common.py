"""
Common handlers: start, language selection.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from database import User
from utils import (
    get_language_selection_keyboard, get_main_menu_keyboard,
    Localization, KeyboardLoader, bot_logger, get_bot_statistics
)
from .db_helpers import get_db_session, get_or_create_user

logger = logging.getLogger(__name__)
router = Router()

# Initialize localization
localization = Localization()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Handle /start command."""
    if not message.from_user:
        return
        
    await state.clear()
    
    with get_db_session() as db:
        user = await get_or_create_user(
            message.from_user.id, 
            message.from_user.username, 
            message.from_user.full_name,
            db
        )
        
        # Always show language selection on /start
        welcome_text = localization.get_text("welcome.choose_language", "ru")
        await message.answer(
            welcome_text,
            reply_markup=get_language_selection_keyboard()
        )
    
    bot_logger.log_user_action(message.from_user.id, "start_command", "")


@router.message(F.text.in_(["🇷🇺 Русский", "🇺🇸 English", "🇹🇼 繁體中文"]))
async def language_selection(message: Message, state: FSMContext):
    """Handle language selection."""
    if not message.text or not message.from_user:
        return
    
    # Get all language buttons from keyboard
    lang_buttons_ru = KeyboardLoader.get_all_button_texts("language_selection", "ru")
    
    if message.text not in lang_buttons_ru:
        return
    
    # Map button text to language code
    language_map = {
        "🇷🇺 Русский": "ru",
        "🇺🇸 English": "en",
        "🇹🇼 繁體中文": "zh-tw"
    }
    
    language_code = language_map.get(message.text, "ru")
    
    with get_db_session() as db:
        user = db.query(User).filter(User.id == message.from_user.id).first()
        if user:
            setattr(user, 'language', language_code)
            db.commit()
            
            await state.clear()
            
            # Get statistics for social proof
            stats = get_bot_statistics()
            
            # Welcome message with selected language
            welcome_text = localization.get_text(
                "welcome.start", language_code, 
                user_name=user.full_name or "User",
                total_ads=stats["total_ads"],
                total_users=stats["total_users"]
            )
            
            await message.answer(
                welcome_text,
                reply_markup=get_main_menu_keyboard(language_code),
                parse_mode="HTML"
            )
            
            bot_logger.log_user_action(message.from_user.id, "language_selected", language_code)
