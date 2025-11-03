"""
User handlers for AdDesigner Hub Telegram Bot.
"""

import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils import (
    UserStates, MessageLoader, KeyboardLoader,
    get_main_menu_keyboard, bot_logger,
    get_tariff_selection_keyboard,
    get_ai_processing_keyboard, get_ai_result_keyboard,
    safe_delete_message, send_text_with_image, process_ai_improvement,
    get_user_info_from_message, show_ai_result_with_image, proceed_to_currency_selection
)

from services import ai_service
from bot_config import settings
from .db_helpers import get_db_session, get_or_create_user

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.in_(KeyboardLoader.get_button_texts_all_langs("main_menu", (0, 0))))
async def create_ad_start(message: Message, state: FSMContext):
    """Start ad creation process - request text and optional image."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
        
    # Ask for text and optional image
    message_text = MessageLoader.get_message("ad_creation.paste_text", language)
    
    await message.answer(message_text)
    await state.set_state(UserStates.waiting_for_ad_content)
    
    bot_logger.log_user_action(user_id, "ad_creation_started", "")




@router.message(UserStates.waiting_for_ad_content)
async def receive_ad_content(message: Message, state: FSMContext):
    """Receive ad text and optional image, then show AI processing options."""
    if not message.from_user:
        return
    
    # Extract text
    ad_text = message.text or message.caption or ""
    if not ad_text:
        await message.answer(MessageLoader.get_message("ad_creation.error_no_text"))
        return
    
    # Check for image
    has_image = False
    image_file_id = None
    if message.photo:
        has_image = True
        image_file_id = message.photo[-1].file_id  # Get highest quality
    
    # Save to state
    await state.update_data(
        ad_text=ad_text,
        has_image=has_image,
        image_file_id=image_file_id
    )
    
    # Get user language
    _, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    
    # Show AI processing options (without text preview and stats)
    preview_text = MessageLoader.get_message("ad_creation.choose_ai_option", language)
    
    await message.answer(
        preview_text,
        reply_markup=get_ai_processing_keyboard(language),
        parse_mode="HTML"
    )
    
    await state.set_state(UserStates.ai_processing_choice)




@router.message(UserStates.ai_processing_choice, F.text.in_(KeyboardLoader.get_button_texts_all_langs("ai_processing_options", (0, 0))))
async def process_improve_text(message: Message, state: FSMContext):
    """Improve text with AI."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    data = await state.get_data()
    ad_text = data.get("ad_text", "")
    
    # Show processing message
    processing_text = MessageLoader.get_message("ad_creation.processing_ai", language)
    processing_msg = await message.answer(processing_text)
    
    try:
        # Improve text with AI
        if settings.openai_api_key:
            # Save original text for retry
            await state.update_data(original_ad_text=ad_text)
            
            # Improve text using utility function
            improved_text = await process_ai_improvement(ai_service, ad_text, language)
            
            if not improved_text:
                improved_text = ad_text
            
            # Save to state
            await state.update_data(ad_text=improved_text)
            await safe_delete_message(processing_msg)
            
            # Show AI result with image using utility
            await show_ai_result_with_image(
                message, improved_text, language, data, get_ai_result_keyboard
            )
            
            # Set state to handle AI result actions
            await state.set_state(UserStates.ai_result_confirmation)
            
        else:
            # AI not configured
            await safe_delete_message(processing_msg)
            fallback_text = MessageLoader.get_message("ad_creation.ai_not_configured", language)
            await message.answer(fallback_text, reply_markup=get_ai_processing_keyboard(language))
            
    except Exception as e:
        logger.error(f"Error in AI processing: {e}", exc_info=True)
        await safe_delete_message(processing_msg)
        error_text = MessageLoader.get_message("ad_creation.ai_error", language)
        await message.answer(error_text, reply_markup=get_ai_processing_keyboard(language))




@router.message(UserStates.ai_processing_choice, F.text.in_(KeyboardLoader.get_button_texts_all_langs("ai_processing_options", (1, 0))))
async def process_keep_as_is(message: Message, state: FSMContext):
    """Keep text and image as is, proceed to tariff selection."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    # Show message to open Web App
    approval_text = MessageLoader.get_message("ad_creation.text_approved", language)
    
    await message.answer(
        approval_text,
        reply_markup=get_tariff_selection_keyboard(language),
        parse_mode="HTML"
    )
    
    await state.set_state(UserStates.tariff_selection)


# AI Result Action Handlers (using reply keyboard)


@router.message(UserStates.ai_result_confirmation, F.text.in_(KeyboardLoader.get_button_texts_all_langs("ai_result_confirmation", (0, 0))))
async def handle_ai_continue(message: Message, state: FSMContext):
    """Proceed to tariff selection with current (improved) text."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    # Show message to open Web App
    approval_text = MessageLoader.get_message("ad_creation.text_approved", language)
    
    await message.answer(
        approval_text,
        reply_markup=get_tariff_selection_keyboard(language),
        parse_mode="HTML"
    )
    
    await state.set_state(UserStates.tariff_selection)




@router.message(UserStates.ai_result_confirmation, F.text.in_(KeyboardLoader.get_button_texts_all_langs("ai_result_confirmation", (1, 0))))
async def show_ai_comparison(message: Message, state: FSMContext):
    """Show comparison between original and AI-improved text."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    # Get both original and improved text from state
    state_data = await state.get_data()
    original_text = state_data.get("original_ad_text", state_data.get("ad_text", ""))
    improved_text = state_data.get("ad_text", "")
    
    # Calculate character counts
    original_chars = len(original_text)
    improved_chars = len(improved_text)
    
    # Get comparison message
    comparison_text = MessageLoader.get_message("ad_creation.ai_comparison", language,
        original_text=original_text,
        improved_text=improved_text,
        original_chars=original_chars,
        improved_chars=improved_chars
    )
    
    # Show comparison with same keyboard to allow continuing
    await message.answer(
        comparison_text,
        reply_markup=get_ai_result_keyboard(language),
        parse_mode="HTML"
    )




@router.message(UserStates.ai_result_confirmation, F.text.in_(KeyboardLoader.get_button_texts_all_langs("ai_result_confirmation", (2, 0))))
async def handle_ai_edit(message: Message, state: FSMContext):
    """Allow user to manually edit the improved text."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    data = await state.get_data()
    current_text = data.get("ad_text", "")
    
    # Send instruction
    instruction_text = MessageLoader.get_message("ad_creation.edit_instruction", language)
    await message.answer(instruction_text, parse_mode="HTML")
    
    # Send current text in code block for easy copying
    await message.answer(f"```\n{current_text}\n```", parse_mode="Markdown")
    
    await state.set_state(UserStates.waiting_for_ad_content)




@router.message(UserStates.ai_result_confirmation, F.text.in_(KeyboardLoader.get_button_texts_all_langs("ai_result_confirmation", (3, 0))))
async def handle_ai_retry(message: Message, state: FSMContext):
    """Re-run AI improvement on the original text."""
    user_id, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user_id:
        return
    
    data = await state.get_data()
    # Get original text (stored before AI improvement)
    original_text = data.get("original_ad_text", data.get("ad_text", ""))
    
    # Show processing message
    processing_text = MessageLoader.get_message("ad_creation.processing_ai", language)
    processing_msg = await message.answer(processing_text)
    
    try:
        # Improve text with AI
        if settings.openai_api_key:
            improved_text = await process_ai_improvement(ai_service, original_text, language)
            
            if not improved_text:
                improved_text = original_text
            
            # Save to state
            await state.update_data(ad_text=improved_text)
            await safe_delete_message(processing_msg)
            
            # Show AI result with image using utility
            await show_ai_result_with_image(
                message, improved_text, language, data, get_ai_result_keyboard
            )
            
            await state.set_state(UserStates.ai_result_confirmation)
            
        else:
            # AI not configured
            await safe_delete_message(processing_msg)
            fallback_text = MessageLoader.get_message("ad_creation.ai_not_configured", language)
            await message.answer(fallback_text, reply_markup=get_tariff_selection_keyboard(language))
            await state.set_state(UserStates.tariff_selection)
            
    except Exception as e:
        logger.error(f"Error in AI retry: {e}", exc_info=True)
        await safe_delete_message(processing_msg)
        error_text = MessageLoader.get_message("errors.processing_error", language)
        await message.answer(error_text, reply_markup=get_main_menu_keyboard(language))
        await state.clear()


# ========================= TARIFF & PAYMENT HANDLERS (TEXT-BASED) =========================



