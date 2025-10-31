"""
Localization service for multi-language support.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class LocalizationService:
    """Service for handling multi-language localization."""
    
    def __init__(self, locales_dir: str = "locales"):
        """Initialize localization service."""
        self.locales_dir = Path(locales_dir)
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.default_language = "ru"
        self.supported_languages = ["ru", "en", "zh-tw"]
        
        # Load translations
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files from locales directory."""
        try:
            for lang in self.supported_languages:
                lang_file = self.locales_dir / f"{lang}.yml"
                
                if lang_file.exists():
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang] = yaml.safe_load(f)
                    logger.info(f"Loaded translations for language: {lang}")
                else:
                    logger.warning(f"Translation file not found: {lang_file}")
                    
        except Exception as e:
            logger.error(f"Error loading translations: {e}")
    
    def get_text(self, key: str, lang: str = None, **kwargs) -> str:
        """
        Get localized text by key.
        
        Args:
            key: Translation key (e.g., "menu.submit_ad")
            lang: Language code (e.g., "ru", "en", "zh-tw")
            **kwargs: Variables to format into the text
            
        Returns:
            Localized text string
        """
        if not lang:
            lang = self.default_language
        
        # Get translation from cache
        text = self._get_nested_value(self.translations.get(lang, {}), key)
        
        # Fallback to default language if not found
        if text is None and lang != self.default_language:
            text = self._get_nested_value(self.translations.get(self.default_language, {}), key)
        
        # Final fallback to key itself
        if text is None:
            logger.warning(f"Translation not found: {key} for language: {lang}")
            text = key
        
        # Format with variables if provided
        if kwargs and isinstance(text, str):
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError) as e:
                logger.warning(f"Error formatting translation {key}: {e}")
        
        return str(text)
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    def get_language_name(self, lang: str) -> str:
        """Get human-readable language name."""
        names = {
            "ru": "Русский",
            "en": "English", 
            "zh-tw": "繁體中文"
        }
        return names.get(lang, lang)
    
    def is_supported_language(self, lang: str) -> bool:
        """Check if language is supported."""
        return lang in self.supported_languages
    
    def get_supported_languages(self) -> list[str]:
        """Get list of supported languages."""
        return self.supported_languages.copy()
    
    def reload_translations(self):
        """Reload translation files."""
        self.translations.clear()
        self._load_translations()
    
    def add_translation(self, lang: str, key: str, value: str):
        """Add or update translation dynamically."""
        if lang not in self.translations:
            self.translations[lang] = {}
        
        # Set nested value
        keys = key.split('.')
        current = self.translations[lang]
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_menu_texts(self, lang: str = None) -> Dict[str, str]:
        """Get all menu-related texts."""
        if not lang:
            lang = self.default_language
            
        menu_keys = [
            "menu.submit_ad",
            "menu.my_ads", 
            "menu.tariffs",
            "menu.help",
            "menu.back",
            "menu.cancel",
            "menu.continue",
            "menu.edit",
            "menu.approve",
            "menu.reject"
        ]
        
        return {key: self.get_text(key, lang) for key in menu_keys}
    
    def get_status_text(self, status: str, lang: str = None) -> str:
        """Get localized status text."""
        status_key = f"my_ads.status_{status}"
        return self.get_text(status_key, lang)
    
    def get_currency_text(self, currency: str, lang: str = None) -> str:
        """Get localized currency text."""
        currency_key = f"payment.currency_{currency.lower()}"
        return self.get_text(currency_key, lang)
    
    def get_error_text(self, error_type: str, lang: str = None) -> str:
        """Get localized error text."""
        error_key = f"errors.{error_type}"
        return self.get_text(error_key, lang)


# Global localization service instance
localization = LocalizationService()


def _(key: str, lang: str = None, **kwargs) -> str:
    """
    Shorthand function for getting localized text.
    
    Args:
        key: Translation key
        lang: Language code
        **kwargs: Variables for formatting
        
    Returns:
        Localized text
    """
    return localization.get_text(key, lang, **kwargs)


def get_user_language(user_id: int) -> str:
    """
    Get user's preferred language.
    This would typically query the database for user's language setting.
    For now, returns default language.
    """
    # TODO: Implement database query for user language
    return localization.default_language


def set_user_language(user_id: int, lang: str) -> bool:
    """
    Set user's preferred language.
    This would typically update the database.
    """
    if not localization.is_supported_language(lang):
        return False
    
    # TODO: Implement database update for user language
    return True


class LocalizedFormatter:
    """Helper class for formatting localized messages."""
    
    def __init__(self, lang: str = None):
        """Initialize with specific language."""
        self.lang = lang or localization.default_language
    
    def format_ad_details(self, ad_data: Dict[str, Any]) -> str:
        """Format ad details message."""
        return _(
            "my_ads.ad_details",
            self.lang,
            id=ad_data.get("id"),
            status=self.get_status_text(ad_data.get("status")),
            channel=ad_data.get("channel_name"),
            created=ad_data.get("created_at"),
            tariff=ad_data.get("tariff_name"),
            text=ad_data.get("text", "")[:200]  # Truncate for preview
        )
    
    def format_payment_invoice(self, payment_data: Dict[str, Any]) -> str:
        """Format payment invoice message."""
        return _(
            "payment.invoice_created",
            self.lang,
            amount=payment_data.get("amount"),
            currency=payment_data.get("currency"),
            description=payment_data.get("description")
        )
    
    def format_tariff_details(self, tariff_data: Dict[str, Any]) -> str:
        """Format tariff details message."""
        period = tariff_data.get("period_days")
        if period:
            period_text = _("common.days", self.lang, days=period)
        else:
            period_text = _("common.one_time", self.lang)
            
        return _(
            "tariffs.details",
            self.lang,
            name=tariff_data.get("name"),
            posts=tariff_data.get("posts_limit"),
            period=period_text,
            price=f"{tariff_data.get('price')} {tariff_data.get('currency')}"
        )
    
    def get_status_text(self, status: str) -> str:
        """Get localized status text."""
        return localization.get_status_text(status, self.lang)
    
    def get_currency_text(self, currency: str) -> str:
        """Get localized currency text."""
        return localization.get_currency_text(currency, self.lang)