"""
Unified utilities for AdDesigner Hub Telegram Bot.
All utility functions combined for simplicity.
"""

import logging
import yaml
import json
import os
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
from pathlib import Path

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    WebAppInfo
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

logger = logging.getLogger(__name__)


# ========================= STATISTICS =========================

def get_bot_statistics():
    """Get bot statistics for social proof."""
    try:
        from database import DatabaseManager, User, Ad
        from datetime import datetime, timedelta
        
        db_manager = DatabaseManager()
        with db_manager.get_session() as db:
            total_users = db.query(User).count()
            total_ads = db.query(Ad).count()
            
            # AI improvements counter (approximate based on total ads)
            ai_improvements_today = max(5, int(total_ads * 0.1))  # Approximate 10% of ads improved
            
            return {
                "total_users": total_users,
                "total_ads": total_ads,
                "ai_improvements_today": ai_improvements_today
            }
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        # Fallback to realistic values
        return {
            "total_users": 2847,
            "total_ads": 5621,
            "ai_improvements_today": 127
        }


# ========================= KEYBOARD MANAGER =========================

class KeyboardLoader:
    """Load and manage keyboards from JSON configuration."""
    
    _keyboards = None
    
    @classmethod
    def load_keyboards(cls) -> Dict[str, Any]:
        """Load keyboard layouts from JSON file."""
        if cls._keyboards is None:
            keyboards_path = Path(__file__).parent.parent / "data" / "keyboards.json"
            try:
                with open(keyboards_path, 'r', encoding='utf-8') as f:
                    cls._keyboards = json.load(f)
                logger.info(f"Loaded {len(cls._keyboards)} keyboard configurations")
            except Exception as e:
                logger.error(f"Failed to load keyboards.json: {e}")
                cls._keyboards = {}
        return cls._keyboards
    
    @classmethod
    def get_keyboard(cls, keyboard_name: str, language: str = "ru", resize: bool = True, one_time: bool = False) -> ReplyKeyboardMarkup:
        """
        Get keyboard from JSON configuration.
        
        Args:
            keyboard_name: Name of keyboard from keyboards.json
            language: Language code (ru, en, zh-tw)
            resize: Resize keyboard to fit screen
            one_time: Hide keyboard after button press
            
        Returns:
            ReplyKeyboardMarkup with buttons from JSON
        """
        keyboards = cls.load_keyboards()
        
        if keyboard_name not in keyboards:
            logger.warning(f"Keyboard '{keyboard_name}' not found in keyboards.json")
            return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🏠 Menu")]], resize_keyboard=True)
        
        keyboard_config = keyboards[keyboard_name]
        
        if language not in keyboard_config:
            logger.warning(f"Language '{language}' not found for keyboard '{keyboard_name}', using 'ru'")
            language = "ru"
        
        button_rows = keyboard_config[language]
        
        # Build keyboard from JSON structure
        keyboard_buttons = []
        for row in button_rows:
            button_row = [KeyboardButton(text=btn_text) for btn_text in row]
            keyboard_buttons.append(button_row)
        
        return ReplyKeyboardMarkup(
            keyboard=keyboard_buttons,
            resize_keyboard=resize,
            one_time_keyboard=one_time
        )
    
    @classmethod
    def get_button_text(cls, keyboard_name: str, button_index: tuple, language: str = "ru") -> str:
        """
        Get specific button text from keyboard configuration.
        
        Args:
            keyboard_name: Name of keyboard from keyboards.json
            button_index: Tuple of (row, col) for button position
            language: Language code (ru, en, zh-tw)
            
        Returns:
            Button text string
        """
        keyboards = cls.load_keyboards()
        
        if keyboard_name not in keyboards:
            logger.warning(f"Keyboard '{keyboard_name}' not found")
            return ""
        
        keyboard_config = keyboards[keyboard_name]
        
        if language not in keyboard_config:
            language = "ru"
        
        try:
            row, col = button_index
            return keyboard_config[language][row][col]
        except (IndexError, KeyError):
            logger.warning(f"Button at {button_index} not found in '{keyboard_name}'")
            return ""
    
    @classmethod
    def get_all_button_texts(cls, keyboard_name: str, language: str = "ru") -> List[str]:
        """
        Get all button texts from keyboard as flat list.
        
        Args:
            keyboard_name: Name of keyboard from keyboards.json  
            language: Language code (ru, en, zh-tw)
            
        Returns:
            List of all button texts
        """
        keyboards = cls.load_keyboards()
        
        if keyboard_name not in keyboards:
            return []
        
        keyboard_config = keyboards[keyboard_name]
        
        if language not in keyboard_config:
            language = "ru"
        
        # Flatten all button texts
        all_texts = []
        for row in keyboard_config[language]:
            all_texts.extend(row)
        
        return all_texts
    
    @classmethod
    def get_button_texts_all_langs(cls, keyboard_name: str, button_index: tuple) -> List[str]:
        """
        Get button text in all languages for F.text.in_() filters.
        
        Args:
            keyboard_name: Name of keyboard from keyboards.json
            button_index: Tuple of (row, col) for button position
            
        Returns:
            List of button texts for all languages [ru, en, zh-tw]
        """
        texts = []
        for lang in ["ru", "en", "zh-tw"]:
            text = cls.get_button_text(keyboard_name, button_index, lang)
            if text:
                texts.append(text)
        return texts


class MessageLoader:
    """Load and manage text messages from YAML localization files."""
    
    _localization = None
    
    @classmethod
    def get_localization(cls):
        """Get or create localization instance."""
        if cls._localization is None:
            # Lazy import to avoid circular dependency
            cls._localization = Localization()
        return cls._localization
    
    @classmethod
    def get_message(cls, key: str, language: str = "ru", **kwargs) -> str:
        """
        Get message text from YAML localization files.
        
        Args:
            key: Message key path (e.g., "welcome", "payment.success")
            language: Language code (ru, en, zh-tw)
            **kwargs: Format parameters for the message
            
        Returns:
            Formatted message text
        """
        loc = cls.get_localization()
        return loc.get_text(key, language, **kwargs)


# ========================= FSM STATES =========================

class UserStates(StatesGroup):
    """User FSM states."""
    language_selection = State()
    waiting_for_ad_content = State()  # Waiting for text + optional image
    ai_processing_choice = State()     # Choosing AI processing option
    ai_result_confirmation = State()   # Confirming AI result
    currency_selection = State()       # Choosing currency before tariff
    tariff_selection = State()         # Choosing tariff plan


class PaymentStates(StatesGroup):
    """Payment FSM states."""
    selecting_currency = State()
    payment_method_selection = State()
    payment_processing = State()


class AdminModerationStates(StatesGroup):
    """Admin moderation states."""
    reviewing_ad = State()
    bulk_actions = State()


# ========================= LOCALIZATION =========================

class Localization:
    """Simple localization service."""
    
    def __init__(self):
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.load_translations()
    
    def load_translations(self):
        """Load translations from locale files."""
        try:
            locales_dir = Path("locales")
            if not locales_dir.exists():
                logger.warning("Locales directory not found")
                return
            
            for locale_file in locales_dir.glob("*.yml"):
                language = locale_file.stem
                try:
                    with open(locale_file, 'r', encoding='utf-8') as f:
                        self.translations[language] = yaml.safe_load(f)
                except Exception as e:
                    logger.error(f"Error loading {locale_file}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
    
    def get_text(self, key: str, language: str = "ru", **kwargs) -> str:
        """Get localized text."""
        try:
            # Split key by dots to navigate nested structure
            keys = key.split('.')
            
            # Get language translations
            translations = self.translations.get(language, self.translations.get("ru", {}))
            
            # Navigate through nested keys
            text = translations
            for k in keys:
                if isinstance(text, dict) and k in text:
                    text = text[k]
                else:
                    # Fallback to key if not found
                    text = key
                    break
            
            # If text is still dict, convert to string
            if isinstance(text, dict):
                text = str(text)
            
            # Format with kwargs if provided
            if kwargs and isinstance(text, str):
                try:
                    text = text.format(**kwargs)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Formatting error for key '{key}': {e}. Text: {text[:100]}...")
                    # Return text as is if formatting fails
            
            return str(text)
            
        except Exception as e:
            logger.error(f"Localization error for key '{key}': {e}")
            return key


# ========================= KEYBOARDS =========================

class KeyboardManager:
    """Keyboard generation manager."""
    
    @staticmethod
    def get_main_menu_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
        """Get main menu keyboard from JSON."""
        return KeyboardLoader.get_keyboard("main_menu", language)
    
    @staticmethod
    def get_language_selection_keyboard() -> ReplyKeyboardMarkup:
        """Get language selection keyboard from JSON."""
        return KeyboardLoader.get_keyboard("language_selection", "ru")
    
    @staticmethod
    def get_admin_moderation_keyboard(ad_id: int, language: str = "ru") -> ReplyKeyboardMarkup:
        """Get admin moderation keyboard from JSON."""
        return KeyboardLoader.get_keyboard("admin_moderation", language)
    
    @staticmethod
    def get_currency_selection_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
        """Get currency selection keyboard from JSON."""
        return KeyboardLoader.get_keyboard("currency_selection", language)
    
    @staticmethod
    def get_payment_keyboard(payment_url: str, language: str = "ru") -> InlineKeyboardMarkup:
        """Get payment keyboard."""
        builder = InlineKeyboardBuilder()
        
        pay_text = "💳 Оплатить" if language == "ru" else "💳 Pay"
        check_text = "🔄 Проверить оплату" if language == "ru" else "🔄 Check Payment"
        
        builder.add(InlineKeyboardButton(text=pay_text, url=payment_url))
        builder.add(InlineKeyboardButton(text=check_text, callback_data="check_payment"))
        
        builder.adjust(1)
        return builder.as_markup()


# ========================= LOGGING =========================

class BotLogger:
    """Simple bot logging service."""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('bot.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def log_user_action(self, user_id: int, action: str, details: str = ""):
        """Log user action."""
        logger.info(f"User {user_id} - {action} - {details}")
    
    def log_system_event(self, event: str, details: str = ""):
        """Log system event."""
        logger.info(f"System - {event} - {details}")
    
    def log_error(self, error: str, details: str = ""):
        """Log error."""
        logger.error(f"Error - {error} - {details}")


# ========================= METRICS =========================

class MetricsCollector:
    """Simple metrics collector."""
    
    def __init__(self):
        self.metrics = {
            'users_total': 0,
            'ads_total': 0,
            'payments_total': 0,
            'ai_generations': 0
        }
    
    def increment_counter(self, metric: str, value: int = 1):
        """Increment counter metric."""
        if metric in self.metrics:
            self.metrics[metric] += value
    
    def get_metrics(self) -> Dict[str, int]:
        """Get current metrics."""
        return self.metrics.copy()


# ========================= RECEIPT GENERATOR =========================

class ReceiptGenerator:
    """Simple receipt generator - returns text for Telegram, no file saving."""
    
    @staticmethod
    def generate_receipt(payment_data: Dict[str, Any]) -> str:
        """
        Generate payment receipt text for Telegram.
        Files are stored in Telegram, not on server.
        
        Returns:
            Receipt text ready to send to Telegram
        """
        receipt_text = f"""
📧 PAYMENT RECEIPT / ЧЕК ОБ ОПЛАТЕ

💳 Payment ID: {payment_data.get('id', 'N/A')}
💰 Amount: {payment_data.get('amount', 'N/A')} {payment_data.get('currency', 'N/A')}
📅 Date: {datetime.now().strftime('%d.%m.%Y %H:%M')}
👤 User ID: {payment_data.get('user_id', 'N/A')}

✅ Payment completed successfully
✅ Платеж выполнен успешно

Thank you for using our service!
Спасибо за использование нашего сервиса!
"""
        
        return receipt_text



# ========================= SECURITY =========================

class SecurityManager:
    """Simple security manager."""
    
    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Check if user is admin."""
        from bot_config import settings
        return user_id == settings.admin_id
    
    @staticmethod
    def validate_text_input(text: str) -> bool:
        """Validate text input."""
        if not text or len(text.strip()) == 0:
            return False
        if len(text) > 4000:  # Telegram limit
            return False
        return True
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """Sanitize text input."""
        if not text:
            return ""
        # Remove dangerous characters
        dangerous_chars = ['<script>', '</script>', 'javascript:', 'onclick=']
        sanitized = text
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()


# ========================= CONVENIENCE FUNCTIONS =========================

def setup_logging():
    """Setup logging for the application."""
    bot_logger = BotLogger()
    return bot_logger


def init_metrics(port: int = 8000):
    """Initialize metrics collection."""
    return MetricsCollector()


# ========================= GLOBAL INSTANCES =========================

# Create global instances for easy access
localization = Localization()
bot_logger = BotLogger()
metrics = MetricsCollector()
receipt_generator = ReceiptGenerator()
security = SecurityManager()

# Keyboard convenience functions (for backwards compatibility)
get_main_menu_keyboard = KeyboardManager.get_main_menu_keyboard
get_language_selection_keyboard = KeyboardManager.get_language_selection_keyboard
get_admin_moderation_keyboard = KeyboardManager.get_admin_moderation_keyboard
get_currency_selection_keyboard = KeyboardManager.get_currency_selection_keyboard
get_payment_keyboard = KeyboardManager.get_payment_keyboard

# Admin menu placeholder function
def get_admin_menu_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get admin menu keyboard."""
    builder = ReplyKeyboardBuilder()
    
    builder.add(KeyboardButton(text="📋 Модерация"))
    builder.add(KeyboardButton(text="📊 Статистика"))
    builder.add(KeyboardButton(text="👥 Пользователи"))
    builder.add(KeyboardButton(text="📢 Рассылка"))
    builder.add(KeyboardButton(text="🔙 Назад"))
    
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# Placeholder functions for missing keyboards
def get_ad_preview_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get ad preview keyboard from JSON."""
    return KeyboardLoader.get_keyboard("ad_preview", language)

def get_tariff_selection_keyboard(language: str = "ru", currency: str = "RUB") -> ReplyKeyboardMarkup:
    """
    Get tariff selection keyboard with Web App button only.
    All tariff selection and payment happens in Web App.
    
    Args:
        language: User language (ru, en, zh-tw)
        currency: Selected currency (not used, kept for compatibility)
    
    Returns:
        Keyboard with Web App button and back button
    """
    from aiogram.utils.keyboard import ReplyKeyboardBuilder
    from aiogram.types import KeyboardButton, WebAppInfo
    
    builder = ReplyKeyboardBuilder()
    
    # Web App URL with language parameter - unified order page
    webapp_url = f"https://trava1er.github.io/ad_designer_bot/unified_order.html?lang={language}"
    
    if language == "ru":
        builder.row(KeyboardButton(
            text="💰 Выбрать тариф и оплатить",
            web_app=WebAppInfo(url=webapp_url)
        ))
        builder.row(KeyboardButton(text="🏠 Главное меню"))
    elif language == "en":
        builder.row(KeyboardButton(
            text="💰 Choose plan and pay",
            web_app=WebAppInfo(url=webapp_url)
        ))
        builder.row(KeyboardButton(text="🏠 Main Menu"))
    else:  # zh-tw
        builder.row(KeyboardButton(
            text="💰 選擇方案並付款",
            web_app=WebAppInfo(url=webapp_url)
        ))
        builder.row(KeyboardButton(text="🏠 主選單"))
    
    return builder.as_markup(resize_keyboard=True)

def get_payment_method_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get payment method selection keyboard from JSON."""
    return KeyboardLoader.get_keyboard("payment_method", language)

def get_my_ads_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get my ads management keyboard from JSON."""
    return KeyboardLoader.get_keyboard("my_ads", language)

def get_confirmation_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get confirmation keyboard from JSON."""
    return KeyboardLoader.get_keyboard("confirmation", language)

def get_ad_creation_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get ad creation keyboard from JSON."""
    return KeyboardLoader.get_keyboard("ad_creation", language)

def get_ai_processing_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get AI processing options keyboard from JSON."""
    return KeyboardLoader.get_keyboard("ai_processing_options", language)

def get_ai_result_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get AI result confirmation keyboard from JSON."""
    return KeyboardLoader.get_keyboard("ai_result_confirmation", language)

def get_text_method_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get text method keyboard from JSON."""
    return KeyboardLoader.get_keyboard("text_method", language)

def get_media_method_keyboard(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get media method keyboard from JSON."""
    return KeyboardLoader.get_keyboard("media_method", language)

def get_currency_selection_keyboard_reply(language: str = "ru") -> ReplyKeyboardMarkup:
    """Get currency selection keyboard from JSON (ReplyKeyboard version)."""
    return KeyboardLoader.get_keyboard("currency_selection", language)


# ========================= HELPER UTILITIES =========================

async def safe_delete_message(message) -> bool:
    """
    Safely delete a message without raising exceptions.
    
    Args:
        message: Telegram message object to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        await message.delete()
        return True
    except Exception as e:
        logger.debug(f"Could not delete message: {e}")
        return False


async def send_text_with_image(
    message,
    text: str,
    image_file_id: Optional[str] = None,
    caption: Optional[str] = None,
    reply_markup=None,
    parse_mode: str = "HTML"
):
    """
    Send text with optional image.
    If image is provided, sends text first, then image with caption.
    Otherwise just sends text.
    
    Args:
        message: Message object to reply to
        text: Main text to send
        image_file_id: Optional Telegram file_id for image
        caption: Optional caption for image
        reply_markup: Optional keyboard markup
        parse_mode: Parse mode for text (default: HTML)
    """
    if image_file_id:
        # Send text first
        await message.answer(text, parse_mode=parse_mode)
        # Then image with caption
        await message.answer_photo(
            photo=image_file_id,
            caption=caption or "",
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    else:
        # Just send text
        await message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )


async def process_ai_improvement(
    ai_service,
    original_text: str,
    language: str,
    prompt_key: str = "ai_prompts.improve_service_ad"
) -> Optional[str]:
    """
    Process text with AI improvement.
    Automatically shortens text if it exceeds 950 characters.
    
    Args:
        ai_service: AI service instance
        original_text: Original text to improve
        language: User language
        prompt_key: Message key for AI prompt template
        
    Returns:
        Improved text or None if failed
    """
    try:
        from bot_config import settings
        
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not configured")
            return None
        
        logger.info(f"Starting AI improvement for text ({len(original_text)} chars)")
        
        # First improvement attempt
        prompt = MessageLoader.get_message(prompt_key, language, text=original_text)
        logger.info(f"Generated prompt for AI (first {100} chars): {prompt[:100]}...")
        
        improved_text = await ai_service.generate_text(prompt, language)
        logger.info(f"AI returned text ({len(improved_text) if improved_text else 0} chars): {improved_text[:100] if improved_text else 'None'}...")
        
        # Check if improvement was successful
        if not improved_text or improved_text in ["Ошибка генерации текста", "Text generation error", "文本生成錯誤"]:
            logger.warning("AI improvement failed - returned error or None")
            return None
        
        # Check text length and automatically shorten if needed
        max_retries = 2
        retry_count = 0
        
        while len(improved_text) > 950 and retry_count < max_retries:
            logger.info(f"Text too long ({len(improved_text)} chars), shortening... (attempt {retry_count + 1}/{max_retries})")
            
            # Save current text before attempting shortening
            previous_text = improved_text
            
            # Use shorten prompt
            shorten_prompt = MessageLoader.get_message(
                "ai_prompts.shorten_text", 
                language, 
                text=improved_text,
                length=len(improved_text)
            )
            shortened_text = await ai_service.generate_text(shorten_prompt, language)
            
            if not shortened_text or shortened_text in ["Ошибка генерации текста", "Text generation error", "文本生成錯誤"]:
                # If shortening failed, truncate manually as last resort
                logger.warning("AI shortening failed, truncating manually")
                improved_text = previous_text[:947] + "..."
                break
            
            improved_text = shortened_text
            retry_count += 1
        
        # Final check - if still too long after retries, truncate
        if len(improved_text) > 950:
            logger.warning(f"Text still too long after {max_retries} retries, truncating to 950 chars")
            improved_text = improved_text[:947] + "..."
        
        return improved_text
        
    except Exception as e:
        logger.error(f"AI improvement failed: {e}", exc_info=True)
        return None


async def get_user_info_from_message(message, db_session_func, get_or_create_user_func):
    """
    Extract user and language from message with common validation.
    
    Args:
        message: Telegram message object
        db_session_func: Function to get database session
        get_or_create_user_func: Function to get or create user
        
    Returns:
        tuple: (user_id, language: str) or (None, "ru") if invalid message
    """
    if not message.from_user:
        return None, "ru"
    
    with db_session_func() as db:
        user = await get_or_create_user_func(
            message.from_user.id,
            message.from_user.username or "unknown",
            message.from_user.full_name or "Unknown",
            db
        )
        # Extract data while session is active
        user_id = user.id
        language = str(user.language or "ru")
        # Return simple data, not ORM object
        return user_id, language


async def show_ai_result_with_image(
    message,
    improved_text: str,
    language: str,
    data: dict,
    ai_result_keyboard_func
):
    """
    Show AI-improved text with optional image and action keyboard.
    
    Args:
        message: Message object to reply to
        improved_text: AI-improved text
        language: User language
        data: State data containing image info
        ai_result_keyboard_func: Function to get AI result keyboard
    """
    # Get AI improvements count
    stats = get_bot_statistics()
    ai_improvements_today = stats.get("ai_improvements_today", 5)
    
    # Get message about final version with improved text
    full_text = MessageLoader.get_message(
        "ad_creation.ai_improved", 
        language, 
        improved_text=improved_text,
        ai_improvements_today=ai_improvements_today
    )
    
    # Telegram caption limit is 1024, but we use 950 for safety
    # If full_text exceeds limit, truncate improved_text part
    if len(full_text) > 1024:
        logger.warning(f"Caption too long ({len(full_text)} chars), truncating improved_text")
        # Calculate how much space we need for the template
        template_overhead = len(full_text) - len(improved_text)
        max_improved_text_length = 1024 - template_overhead - 3  # -3 for "..."
        truncated_improved_text = improved_text[:max_improved_text_length] + "..."
        
        full_text = MessageLoader.get_message(
            "ad_creation.ai_improved", 
            language, 
            improved_text=truncated_improved_text,
            ai_improvements_today=ai_improvements_today
        )
    
    # Send with image if user had one
    if data.get("has_image") and data.get("image_file_id"):
        image_file_id = data.get("image_file_id")
        if image_file_id:
            await message.answer_photo(
                photo=image_file_id,
                caption=full_text,
                reply_markup=ai_result_keyboard_func(language),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                full_text,
                reply_markup=ai_result_keyboard_func(language),
                parse_mode="HTML"
            )
    else:
        await message.answer(
            full_text,
            reply_markup=ai_result_keyboard_func(language),
            parse_mode="HTML"
        )


async def proceed_to_currency_selection(
    message,
    language: str,
    state
):
    """
    Show currency selection before tariffs.
    
    Args:
        message: Message object to reply to
        language: User language
        state: FSM state context
    """
    currency_text = MessageLoader.get_message("payment.choose_currency", language)
    currency_keyboard = get_currency_selection_keyboard_reply(language)
    
    await message.answer(
        currency_text,
        reply_markup=currency_keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(UserStates.currency_selection)


async def proceed_to_tariff_selection(
    message,
    language: str,
    currency: str,
    state
):
    """
    Proceed to tariff selection with selected currency.
    Shows visual tariff comparison image if available, otherwise text.
    
    Args:
        message: Message object to reply to
        language: User language
        currency: Selected currency (RUB, USD, USDT)
        state: FSM state context
    """
    from aiogram.types import FSInputFile
    import os
    
    # Get statistics for social proof
    stats = get_bot_statistics()
    
    pricing_text = MessageLoader.get_message(
        "tariffs.choose_tariff", 
        language,
        ads_today=stats.get("total_ads", 127)  # Total ads as proxy for today's activity
    )
    tariff_keyboard = get_tariff_selection_keyboard(language, currency)
    
    # Try to send visual comparison image
    comparison_image_path = f"images/tariffs/comparison_{language}_{currency}.png"
    fallback_comparison = "images/tariffs/comparison.png"
    
    image_sent = False
    for image_path in [comparison_image_path, fallback_comparison]:
        if os.path.exists(image_path):
            try:
                photo = FSInputFile(image_path)
                await message.answer_photo(
                    photo=photo,
                    caption=pricing_text,
                    reply_markup=tariff_keyboard,
                    parse_mode="HTML"
                )
                image_sent = True
                break
            except Exception as e:
                logger.error(f"Failed to send tariff image {image_path}: {e}")
    
    # Fallback to text if no image available
    if not image_sent:
        await message.answer(
            pricing_text,
            reply_markup=tariff_keyboard,
            parse_mode="HTML"
        )
    
    await state.set_state(UserStates.tariff_selection)


async def handle_tariff_selection(
    message,
    state: FSMContext,
    plan_name: str,
    plan_details: dict,
    get_user_func,
    get_db_func,
    payment_keyboard_func
):
    """
    Universal handler for tariff plan selection.
    
    Args:
        message: Message object
        state: FSM state
        plan_name: Name of the plan (single/month/premium)
        plan_details: Dict with price, period_days, ads_count
        get_user_func: Function to get user and language
        get_db_func: Function to get DB session
        payment_keyboard_func: Function to get payment method keyboard
    """
    if not message.from_user:
        return
    
    with get_db_func() as db:
        user, language = get_user_func(db, message.from_user.id)
        
        # Save tariff details
        await state.update_data(
            selected_plan=plan_name,
            selected_tariff=plan_details
        )
        
        # Set state to payment method selection
        await state.set_state(PaymentStates.payment_method_selection)
        
        payment_text = MessageLoader.get_message("payment.choose_method", language)
        
        await message.answer(
            payment_text,
            reply_markup=payment_keyboard_func(language)
        )