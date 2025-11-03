"""
Unified services for AdDesigner Hub Telegram Bot.
All business logic services combined for simplicity.
"""

import logging
import asyncio
from openai import AsyncOpenAI
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

from bot_config import settings

logger = logging.getLogger(__name__)

# Configure OpenAI
client = AsyncOpenAI(api_key=settings.openai_api_key)


class AIService:
    """Unified AI service for text and image generation."""
    
    @staticmethod
    def _format_ad_text(text: str) -> str:
        """
        Format AI-generated text to ensure professional appearance.
        Adds proper line breaks and spacing if missing.
        """
        if not text:
            return text
        
        # Remove excessive whitespace but preserve intentional line breaks
        lines = [line.strip() for line in text.split('\n')]
        
        # If text is one long paragraph, try to add structure
        if len(lines) <= 2 and len(text) > 200:
            # Look for emoji markers that should start new sections
            import re
            # Split on emoji patterns (common section markers)
            sections = re.split(r'(\n|(?=[💼🛠⚡✅📍📩🎯🔥💡👉📞✉️🌟]))', text)
            formatted_lines = []
            for section in sections:
                section = section.strip()
                if section and section not in ['\n']:
                    formatted_lines.append(section)
            
            # Join with proper spacing
            result = '\n\n'.join(formatted_lines) if len(formatted_lines) > 1 else text
        else:
            # Join existing lines with single line breaks, add double breaks between major sections
            result = []
            for i, line in enumerate(lines):
                if line:
                    result.append(line)
                    # Add extra spacing after lines with emojis (section headers)
                    if any(emoji in line for emoji in ['💼', '🛠', '⚡', '✅', '📍', '📩']):
                        result.append('')  # Empty line for spacing
            result = '\n'.join(result)
        
        return result
    
    @staticmethod
    async def generate_text(prompt: str, language: str = "ru") -> str:
        """Generate text using OpenAI GPT."""
        try:
            if language == "ru":
                system_prompt = "Ты — креативный копирайтер. Создавай привлекательные рекламные тексты."
            elif language == "en":
                system_prompt = "You are a creative copywriter. Create engaging advertising texts."
            else:
                system_prompt = "您是一位創意文案作家。創建引人入勝的廣告文案。"
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            if content:
                # Format the text for better visual appearance
                formatted_text = AIService._format_ad_text(content.strip())
                return formatted_text
            return ""
            
        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return "Ошибка генерации текста" if language == "ru" else "Text generation error"
    
    @staticmethod
    async def generate_image(prompt: str, style: str = "realistic") -> Optional[str]:
        """Generate image using DALL-E."""
        try:
            style_prompts = {
                "realistic": "photorealistic, high quality, detailed",
                "cartoon": "cartoon style, colorful, vector art",
                "minimalist": "minimalist, clean, simple design",
                "vintage": "vintage style, retro, aged look"
            }
            
            enhanced_prompt = f"{prompt}, {style_prompts.get(style, '')}"
            
            response = await client.images.generate(
                prompt=enhanced_prompt,
                n=1,
                size="1024x1024"
            )
            
            if response and response.data and len(response.data) > 0:
                return response.data[0].url
            else:
                return None
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None


class PaymentService:
    """Unified payment service for all providers."""
    
    @staticmethod
    async def create_payment(amount: Decimal, currency: str, description: str, user_id: int) -> Optional[str]:
        """Create payment with appropriate provider."""
        try:
            if currency == "RUB":
                return await PaymentService._create_yookassa_payment(amount, description, user_id)
            elif currency == "USD":
                return await PaymentService._create_stripe_payment(amount, description, user_id)
            elif currency == "USDT":
                return await PaymentService._create_crypto_payment(amount, description, user_id)
            
        except Exception as e:
            logger.error(f"Payment creation error: {e}")
            return None
    
    @staticmethod
    async def _create_yookassa_payment(amount: Decimal, description: str, user_id: int) -> Optional[str]:
        """Create YooKassa payment."""
        # Demo implementation
        return f"https://demo-payment.yookassa.ru/{user_id}_{amount}"
    
    @staticmethod
    async def _create_stripe_payment(amount: Decimal, description: str, user_id: int) -> Optional[str]:
        """Create Stripe payment."""
        # Demo implementation
        return f"https://checkout.stripe.com/demo/{user_id}_{amount}"
    
    @staticmethod
    async def _create_crypto_payment(amount: Decimal, description: str, user_id: int) -> Optional[str]:
        """Create crypto payment."""
        # Demo implementation
        return f"https://nowpayments.io/demo/{user_id}_{amount}"
    
    @staticmethod
    async def check_payment_status(payment_id: str, provider: str) -> bool:
        """Check payment status."""
        # Demo implementation - always return True after delay
        await asyncio.sleep(1)
        return True


class NotificationService:
    """Service for sending notifications."""
    
    @staticmethod
    async def send_ad_approved(user_id: int, ad_id: int, language: str = "ru"):
        """Send ad approval notification."""
        try:
            from aiogram import Bot
            
            bot = Bot(token=settings.telegram_bot_token)
            
            if language == "ru":
                message = f"✅ Ваше объявление #{ad_id} одобрено и опубликовано!"
            elif language == "en":
                message = f"✅ Your advertisement #{ad_id} has been approved and published!"
            else:
                message = f"✅ 您的廣告 #{ad_id} 已獲批准並發布！"
            
            await bot.send_message(chat_id=user_id, text=message)
            
        except Exception as e:
            logger.error(f"Notification error: {e}")
    
    @staticmethod
    async def send_ad_rejected(user_id: int, ad_id: int, reason: str, language: str = "ru"):
        """Send ad rejection notification."""
        try:
            from aiogram import Bot
            
            bot = Bot(token=settings.telegram_bot_token)
            
            if language == "ru":
                message = f"❌ Ваше объявление #{ad_id} отклонено.\n\nПричина: {reason}"
            elif language == "en":
                message = f"❌ Your advertisement #{ad_id} has been rejected.\n\nReason: {reason}"
            else:
                message = f"❌ 您的廣告 #{ad_id} 已被拒絕。\n\n原因：{reason}"
            
            await bot.send_message(chat_id=user_id, text=message)
            
        except Exception as e:
            logger.error(f"Notification error: {e}")


class PublicationService:
    """Service for publishing ads to channels."""
    
    @staticmethod
    async def publish_ad(ad_id: int, text: str, media: Optional[List] = None):
        """Publish ad to target channel. Returns (channel_username, channel_id, message_id)."""
        try:
            from aiogram import Bot
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            from bot_config import settings
            
            bot = Bot(token=settings.telegram_bot_token)
            
            # Use channel_id_default from config (matches .env CHANNEL_ID_DEFAULT)
            channel_id = settings.channel_id_default
            
            # Get bot username for the link
            bot_info = await bot.get_me()
            bot_username = bot_info.username
            
            # Create inline keyboard with button to bot
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="📝 Создать объявление",
                            url=f"https://t.me/{bot_username}"
                        )
                    ]
                ]
            )
            
            if media and len(media) > 0:
                # Send with media
                sent_message = await bot.send_photo(
                    chat_id=channel_id,
                    photo=media[0],
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            else:
                # Send text only
                sent_message = await bot.send_message(
                    chat_id=channel_id,
                    text=text,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
            
            logger.info(f"Ad {ad_id} published to channel {channel_id}")
            
            # Get channel info for username
            channel_username = None
            try:
                channel_info = await bot.get_chat(channel_id)
                channel_username = getattr(channel_info, 'username', None)
                
                logger.info(f"[DEBUG] Channel info: username={channel_username}, channel_id={channel_id}")
                        
            except Exception as e:
                logger.warning(f"Could not get channel info: {e}")
            
            # Close bot session
            await bot.session.close()
            
            return (channel_username, channel_id, sent_message.message_id)
            
        except Exception as e:
            logger.error(f"Publication error: {e}")
            raise  # Re-raise to handle in caller


class ReceiptService:
    """Service for generating payment receipts."""
    
    @staticmethod
    async def generate_receipt_text(payment_id: int, amount: Decimal, currency: str, user_id: int) -> str:
        """
        Generate receipt text for Telegram.
        No files saved on server - only sent to Telegram.
        
        Returns:
            Receipt text ready to send
        """
        receipt_data = {
            "payment_id": payment_id,
            "amount": str(amount),
            "currency": currency,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "user_id": user_id
        }
        
        receipt_text = f"""
📧 RECEIPT / ЧЕК

💳 Payment ID: {payment_id}
💰 Amount: {amount} {currency}
📅 Date: {receipt_data['date']}
👤 User: {user_id}

✅ Payment completed successfully
"""
        
        return receipt_text


# Convenience instances
ai_service = AIService()
payment_service = PaymentService()
notification_service = NotificationService()
publication_service = PublicationService()
receipt_service = ReceiptService()


# Legacy compatibility
class OpenAITextService:
    """Legacy compatibility class."""
    @staticmethod
    async def generate_text(prompt: str, language: str = "ru") -> str:
        return await ai_service.generate_text(prompt, language)

class OpenAIImageService:
    """Legacy compatibility class."""
    @staticmethod
    async def generate_image(prompt: str, style: str = "realistic") -> Optional[str]:
        return await ai_service.generate_image(prompt, style)

# Legacy instances
openai_text_service = OpenAITextService()
openai_image_service = OpenAIImageService()
image_service = ai_service