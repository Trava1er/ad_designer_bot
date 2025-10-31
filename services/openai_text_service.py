"""
OpenAI text generation service for creating ad content.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from dataclasses import dataclass

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class TextGenerationResult:
    """Result of text generation operation."""
    success: bool
    text: Optional[str] = None
    error_message: Optional[str] = None
    tokens_used: int = 0
    model_used: Optional[str] = None


class OpenAITextService:
    """Service for generating ad text using OpenAI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI text service."""
        self.api_key = api_key or settings.openai_api_key
        self.client = None
        
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI API key not provided")
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.client is not None and settings.enable_openai_text
    
    async def generate_ad_text(self, data: Dict[str, Any], lang: str = "ru") -> TextGenerationResult:
        """
        Generate advertisement text using OpenAI.
        
        Args:
            data: Dictionary with ad information
            lang: Language code (ru, en, zh-tw)
            
        Returns:
            TextGenerationResult with generated text
        """
        if not self.is_available():
            return self._fallback_text_generation(data, lang)
        
        try:
            # Create prompt based on language
            prompt = self._create_prompt(data, lang)
            
            # Generate text using OpenAI
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(lang)
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=settings.openai_max_tokens,
                temperature=0.7,
                frequency_penalty=0.2,
                presence_penalty=0.1
            )
            
            # Extract generated text
            generated_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            # Validate length
            if len(generated_text) > settings.max_ad_text_length:
                generated_text = generated_text[:settings.max_ad_text_length - 3] + "..."
            
            return TextGenerationResult(
                success=True,
                text=generated_text,
                tokens_used=tokens_used,
                model_used=settings.openai_model
            )
            
        except Exception as e:
            logger.error(f"OpenAI text generation error: {e}")
            return self._fallback_text_generation(data, lang)
    
    def _create_prompt(self, data: Dict[str, Any], lang: str) -> str:
        """Create prompt for text generation."""
        what = data.get("what", "")
        for_whom = data.get("for_whom", "")
        benefits = data.get("benefits", "")
        contacts = data.get("contacts", "")
        price = data.get("price", "")
        
        if lang == "ru":
            prompt = f"""
            Создай рекламный текст для Telegram канала на основе следующей информации:
            
            Что предлагается: {what}
            Для кого: {for_whom}
            Преимущества: {benefits}
            Контакты: {contacts}
            Цена: {price}
            
            Требования:
            - Максимум 900 символов
            - Привлекательный и убедительный стиль
            - Включи эмодзи для привлечения внимания
            - Структурированный текст с абзацами
            - Призыв к действию в конце
            """
        elif lang == "en":
            prompt = f"""
            Create promotional text for Telegram channel based on this information:
            
            What is offered: {what}
            Target audience: {for_whom}
            Benefits: {benefits}
            Contacts: {contacts}
            Price: {price}
            
            Requirements:
            - Maximum 900 characters
            - Attractive and persuasive style
            - Include emojis for attention
            - Structured text with paragraphs
            - Call to action at the end
            """
        elif lang == "zh-tw":
            prompt = f"""
            根據以下信息為Telegram頻道創建宣傳文字：
            
            提供內容: {what}
            目標受眾: {for_whom}
            優勢: {benefits}
            聯繫方式: {contacts}
            價格: {price}
            
            要求：
            - 最多900字符
            - 吸引人且有說服力的風格
            - 包含表情符號以引起注意
            - 結構化文本與段落
            - 結尾有行動呼籲
            """
        else:
            # Default to English
            prompt = f"""
            Create promotional text for Telegram channel based on this information:
            
            What is offered: {what}
            Target audience: {for_whom}
            Benefits: {benefits}
            Contacts: {contacts}
            Price: {price}
            
            Requirements:
            - Maximum 900 characters
            - Attractive and persuasive style
            - Include emojis for attention
            - Structured text with paragraphs
            - Call to action at the end
            """
        
        return prompt
    
    def _get_system_prompt(self, lang: str) -> str:
        """Get system prompt for different languages."""
        if lang == "ru":
            return """Ты профессиональный копирайтер, специализирующийся на создании рекламных текстов для Telegram каналов. 
            Создавай короткие, яркие и убедительные тексты, которые привлекают внимание и мотивируют к действию. 
            Используй современный интернет-сленг и эмодзи умеренно."""
        elif lang == "en":
            return """You are a professional copywriter specializing in creating promotional texts for Telegram channels. 
            Create short, bright and persuasive texts that attract attention and motivate action. 
            Use modern internet slang and emojis moderately."""
        elif lang == "zh-tw":
            return """你是專業的文案寫手，專門為Telegram頻道創建宣傳文字。
            創建簡短、明亮且有說服力的文本，吸引注意力並激發行動。
            適度使用現代網路俚語和表情符號。"""
        else:
            return """You are a professional copywriter specializing in creating promotional texts for Telegram channels. 
            Create short, bright and persuasive texts that attract attention and motivate action. 
            Use modern internet slang and emojis moderately."""
    
    def _fallback_text_generation(self, data: Dict[str, Any], lang: str) -> TextGenerationResult:
        """Fallback text generation using templates."""
        try:
            template = self._get_template(lang)
            
            # Fill template with data
            text = template.format(
                what=data.get("what", ""),
                for_whom=data.get("for_whom", ""),
                benefits=data.get("benefits", ""),
                contacts=data.get("contacts", ""),
                price=data.get("price", "")
            )
            
            # Clean up empty lines
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            return TextGenerationResult(
                success=True,
                text=text,
                tokens_used=0,
                model_used="template"
            )
            
        except Exception as e:
            logger.error(f"Fallback text generation error: {e}")
            return TextGenerationResult(
                success=False,
                error_message="Text generation failed"
            )
    
    def _get_template(self, lang: str) -> str:
        """Get template for fallback text generation."""
        if lang == "ru":
            return """🎯 {what}

👥 Для кого: {for_whom}

✨ Преимущества:
{benefits}

💰 Цена: {price}

📞 Контакты: {contacts}

🚀 Не упустите возможность! Свяжитесь с нами прямо сейчас!"""
        elif lang == "en":
            return """🎯 {what}

👥 For: {for_whom}

✨ Benefits:
{benefits}

💰 Price: {price}

📞 Contacts: {contacts}

🚀 Don't miss the opportunity! Contact us right now!"""
        elif lang == "zh-tw":
            return """🎯 {what}

👥 適合對象: {for_whom}

✨ 優勢:
{benefits}

💰 價格: {price}

📞 聯繫方式: {contacts}

🚀 不要錯過機會！立即聯繫我們！"""
        else:
            return """🎯 {what}

👥 For: {for_whom}

✨ Benefits:
{benefits}

💰 Price: {price}

📞 Contacts: {contacts}

🚀 Don't miss the opportunity! Contact us right now!"""
    
    async def improve_text(self, original_text: str, lang: str = "ru") -> TextGenerationResult:
        """Improve existing ad text."""
        if not self.is_available():
            return TextGenerationResult(
                success=False,
                error_message="OpenAI service not available"
            )
        
        try:
            prompt = self._create_improvement_prompt(original_text, lang)
            
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(lang)
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=settings.openai_max_tokens,
                temperature=0.5
            )
            
            improved_text = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            return TextGenerationResult(
                success=True,
                text=improved_text,
                tokens_used=tokens_used,
                model_used=settings.openai_model
            )
            
        except Exception as e:
            logger.error(f"Text improvement error: {e}")
            return TextGenerationResult(
                success=False,
                error_message=f"Text improvement failed: {str(e)}"
            )
    
    def _create_improvement_prompt(self, text: str, lang: str) -> str:
        """Create prompt for text improvement."""
        if lang == "ru":
            return f"""Улучши следующий рекламный текст, сделай его более привлекательным и убедительным:

{text}

Требования:
- Максимум 900 символов
- Сохрани основной смысл
- Улучши структуру и читаемость
- Добавь больше привлекательности
- Используй эмодзи умеренно"""
        elif lang == "en":
            return f"""Improve the following promotional text, make it more attractive and persuasive:

{text}

Requirements:
- Maximum 900 characters
- Keep the main meaning
- Improve structure and readability
- Add more attractiveness
- Use emojis moderately"""
        elif lang == "zh-tw":
            return f"""改善以下宣傳文字，使其更具吸引力和說服力：

{text}

要求：
- 最多900字符
- 保持主要意思
- 改善結構和可讀性
- 增加更多吸引力
- 適度使用表情符號"""
        else:
            return f"""Improve the following promotional text, make it more attractive and persuasive:

{text}

Requirements:
- Maximum 900 characters
- Keep the main meaning
- Improve structure and readability
- Add more attractiveness
- Use emojis moderately"""
    
    async def generate_variations(self, base_text: str, count: int = 3, lang: str = "ru") -> List[TextGenerationResult]:
        """Generate multiple variations of the text."""
        if not self.is_available():
            return [TextGenerationResult(success=False, error_message="OpenAI service not available")]
        
        variations = []
        
        for i in range(count):
            try:
                result = await self.improve_text(base_text, lang)
                variations.append(result)
                
                # Add small delay to avoid rate limiting
                if i < count - 1:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Variation generation error: {e}")
                variations.append(TextGenerationResult(
                    success=False,
                    error_message=f"Variation {i+1} failed"
                ))
        
        return variations