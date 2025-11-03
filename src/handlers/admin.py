"""
Admin handlers for AdDesigner Hub Telegram Bot.
"""

import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import DatabaseManager, User, Ad, AdStatusEnum
from utils import (
    get_admin_menu_keyboard,
    MessageLoader, AdminModerationStates, 
    bot_logger, get_admin_moderation_keyboard
)

from bot_config import settings

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    """Admin panel access."""
    if not message.from_user or message.from_user.id != settings.admin_id:
        await message.answer(MessageLoader.get_message("admin.access_denied"))
        return
    
    await message.answer(
        MessageLoader.get_message("admin.panel_title"),
        reply_markup=get_admin_menu_keyboard()
    )
    bot_logger.log_user_action(message.from_user.id, "admin_panel_opened", "")




@router.message(F.text == "📋 Модерация")
async def moderation_menu(message: Message, state: FSMContext):
    """Handle moderation menu."""
    if not message.from_user or message.from_user.id != settings.admin_id:
        return
        
    await show_next_ad_for_moderation(message, state)


async def show_next_ad_for_moderation(message: Message, state: FSMContext):
    """Show next ad for moderation."""
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as db:
        ad = db.query(Ad).filter(Ad.status == AdStatusEnum.PENDING).first()
        
        if not ad:
            await message.answer(MessageLoader.get_message("admin.no_ads_for_moderation"))
            return
        
        # Get ad author
        author = db.query(User).filter(User.id == ad.user_id).first()
        
        ad_text = f"""
🔍 <b>Модерация объявления #{getattr(ad, 'id', 0)}</b>

👤 <b>Автор:</b> {author.full_name if author else 'Unknown'} (@{getattr(author, 'username', None) or 'без username'})
📅 <b>Дата:</b> {ad.created_at.strftime('%d.%m.%Y %H:%M')}

📝 <b>Текст:</b>
{ad.text}
        """
        
        # Handle media
        if hasattr(ad, 'media') and ad.media is not None:
            try:
                if isinstance(ad.media, list) and len(ad.media) > 0:
                    ad_text += f"\n📎 <b>Медиа:</b> {len(ad.media)} файлов"
                elif isinstance(ad.media, str):
                    ad_text += f"\n📎 <b>Медиа:</b> 1 файл"
            except:
                pass
        
        await message.answer(
            ad_text,
            reply_markup=get_admin_moderation_keyboard(getattr(ad, 'id', 0), "ru"),
            parse_mode="HTML"
        )
        
        await state.set_state(AdminModerationStates.reviewing_ad)
        await state.update_data(current_ad_id=getattr(ad, 'id', 0))


# ========================= PAYMENT HANDLERS =========================



