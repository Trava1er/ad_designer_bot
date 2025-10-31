"""
OpenAI image generation service for creating ad visuals.
"""

import asyncio
import logging
import uuid
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class ImageGenerationResult:
    """Result of image generation operation."""
    success: bool
    image_url: Optional[str] = None
    image_data: Optional[bytes] = None
    local_path: Optional[str] = None
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    prompt_used: Optional[str] = None


class OpenAIImageService:
    """Service for generating images using OpenAI DALL-E."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI image service."""
        self.api_key = api_key or settings.openai_api_key
        self.client = None
        self.images_dir = Path("images/generated")
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI API key not provided")
    
    def is_available(self) -> bool:
        """Check if OpenAI image service is available."""
        return self.client is not None and settings.enable_openai_images
    
    async def generate_image_from_text(self, text: str, lang: str = "ru") -> ImageGenerationResult:
        """
        Generate image from ad text using DALL-E.
        
        Args:
            text: Advertisement text
            lang: Language code
            
        Returns:
            ImageGenerationResult with generated image
        """
        if not self.is_available():
            return ImageGenerationResult(
                success=False,
                error_message="OpenAI image service not available"
            )
        
        try:
            # Create image prompt from text
            prompt = self._create_image_prompt(text, lang)
            
            # Generate image using DALL-E
            response = await self.client.images.generate(
                model=settings.openai_image_model,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            # Get image URL
            image_url = response.data[0].url
            
            # Download and save image
            image_data, local_path = await self._download_and_save_image(image_url)
            
            return ImageGenerationResult(
                success=True,
                image_url=image_url,
                image_data=image_data,
                local_path=local_path,
                model_used=settings.openai_image_model,
                prompt_used=prompt
            )
            
        except Exception as e:
            logger.error(f"OpenAI image generation error: {e}")
            return ImageGenerationResult(
                success=False,
                error_message=f"Image generation failed: {str(e)}"
            )
    
    async def generate_image_from_description(self, description: str, style: str = "modern", lang: str = "ru") -> ImageGenerationResult:
        """
        Generate image from description with specific style.
        
        Args:
            description: Image description
            style: Image style (modern, minimalist, colorful, etc.)
            lang: Language code
            
        Returns:
            ImageGenerationResult with generated image
        """
        if not self.is_available():
            return ImageGenerationResult(
                success=False,
                error_message="OpenAI image service not available"
            )
        
        try:
            # Create detailed prompt
            prompt = self._create_styled_prompt(description, style, lang)
            
            response = await self.client.images.generate(
                model=settings.openai_image_model,
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            image_data, local_path = await self._download_and_save_image(image_url)
            
            return ImageGenerationResult(
                success=True,
                image_url=image_url,
                image_data=image_data,
                local_path=local_path,
                model_used=settings.openai_image_model,
                prompt_used=prompt
            )
            
        except Exception as e:
            logger.error(f"Image generation from description error: {e}")
            return ImageGenerationResult(
                success=False,
                error_message=f"Image generation failed: {str(e)}"
            )
    
    def _create_image_prompt(self, text: str, lang: str) -> str:
        """Create image generation prompt from ad text."""
        # Extract key concepts from text (simplified approach)
        text_lower = text.lower()
        
        # Common keywords that suggest image style
        if any(word in text_lower for word in ["дизайн", "design", "設計"]):
            base_prompt = "Professional design concept illustration"
        elif any(word in text_lower for word in ["услуг", "service", "服務"]):
            base_prompt = "Professional service illustration"
        elif any(word in text_lower for word in ["продукт", "product", "產品"]):
            base_prompt = "Product showcase illustration"
        elif any(word in text_lower for word in ["обучен", "education", "learn", "教育"]):
            base_prompt = "Educational concept illustration"
        else:
            base_prompt = "Professional business illustration"
        
        # Add style specifications
        style_additions = [
            "modern minimalist style",
            "clean professional look",
            "bright colors",
            "vector art style",
            "suitable for advertisement",
            "high quality",
            "commercial use"
        ]
        
        prompt = f"{base_prompt}, {', '.join(style_additions)}"
        
        # Limit prompt length
        if len(prompt) > 400:
            prompt = prompt[:400]
        
        return prompt
    
    def _create_styled_prompt(self, description: str, style: str, lang: str) -> str:
        """Create styled image prompt."""
        style_mappings = {
            "modern": "modern minimalist style, clean lines, contemporary design",
            "colorful": "vibrant colors, energetic, bright and cheerful",
            "minimalist": "minimalist design, simple, clean, elegant",
            "professional": "professional business style, corporate, sophisticated",
            "creative": "creative and artistic, unique design, innovative",
            "tech": "technology theme, digital, futuristic, high-tech",
            "vintage": "vintage style, retro design, classic look"
        }
        
        style_desc = style_mappings.get(style, style_mappings["modern"])
        
        prompt = f"{description}, {style_desc}, high quality, commercial use, advertisement ready"
        
        # Add language-specific improvements
        if lang == "ru":
            prompt += ", suitable for Russian market"
        elif lang == "zh-tw":
            prompt += ", suitable for Asian market"
        
        return prompt[:400]  # Limit length
    
    async def _download_and_save_image(self, image_url: str) -> tuple[bytes, str]:
        """Download image and save to local storage."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, timeout=60.0)
                response.raise_for_status()
                
                image_data = response.content
                
                # Generate unique filename
                filename = f"generated_{uuid.uuid4().hex[:8]}.png"
                local_path = self.images_dir / filename
                
                # Save to file
                with open(local_path, "wb") as f:
                    f.write(image_data)
                
                return image_data, str(local_path)
                
        except Exception as e:
            logger.error(f"Image download error: {e}")
            raise
    
    async def create_variation(self, image_path: str) -> ImageGenerationResult:
        """Create variation of existing image."""
        if not self.is_available():
            return ImageGenerationResult(
                success=False,
                error_message="OpenAI image service not available"
            )
        
        try:
            # Read image file
            with open(image_path, "rb") as image_file:
                response = await self.client.images.create_variation(
                    image=image_file,
                    n=1,
                    size="1024x1024"
                )
            
            image_url = response.data[0].url
            image_data, local_path = await self._download_and_save_image(image_url)
            
            return ImageGenerationResult(
                success=True,
                image_url=image_url,
                image_data=image_data,
                local_path=local_path,
                model_used="dall-e-variation"
            )
            
        except Exception as e:
            logger.error(f"Image variation error: {e}")
            return ImageGenerationResult(
                success=False,
                error_message=f"Image variation failed: {str(e)}"
            )
    
    async def edit_image(self, image_path: str, mask_path: str, prompt: str) -> ImageGenerationResult:
        """Edit image using mask and prompt."""
        if not self.is_available():
            return ImageGenerationResult(
                success=False,
                error_message="OpenAI image service not available"
            )
        
        try:
            with open(image_path, "rb") as image_file, open(mask_path, "rb") as mask_file:
                response = await self.client.images.edit(
                    image=image_file,
                    mask=mask_file,
                    prompt=prompt,
                    n=1,
                    size="1024x1024"
                )
            
            image_url = response.data[0].url
            image_data, local_path = await self._download_and_save_image(image_url)
            
            return ImageGenerationResult(
                success=True,
                image_url=image_url,
                image_data=image_data,
                local_path=local_path,
                model_used="dall-e-edit",
                prompt_used=prompt
            )
            
        except Exception as e:
            logger.error(f"Image edit error: {e}")
            return ImageGenerationResult(
                success=False,
                error_message=f"Image edit failed: {str(e)}"
            )
    
    def get_suggested_prompts(self, category: str, lang: str = "ru") -> list[str]:
        """Get suggested image prompts for different categories."""
        prompts = {
            "ru": {
                "design": [
                    "Современный дизайн логотипа",
                    "Минималистичная иллюстрация",
                    "Креативная концепция брендинга"
                ],
                "business": [
                    "Профессиональная бизнес иллюстрация",
                    "Корпоративный стиль",
                    "Деловая презентация"
                ],
                "tech": [
                    "Технологическая концепция",
                    "Цифровая иллюстрация",
                    "Футуристический дизайн"
                ]
            },
            "en": {
                "design": [
                    "Modern logo design",
                    "Minimalist illustration",
                    "Creative branding concept"
                ],
                "business": [
                    "Professional business illustration",
                    "Corporate style",
                    "Business presentation"
                ],
                "tech": [
                    "Technology concept",
                    "Digital illustration",
                    "Futuristic design"
                ]
            }
        }
        
        return prompts.get(lang, prompts["en"]).get(category, [])
    
    def cleanup_old_images(self, days_old: int = 7):
        """Clean up old generated images."""
        try:
            import time
            current_time = time.time()
            
            for image_file in self.images_dir.glob("*.png"):
                file_age = current_time - image_file.stat().st_mtime
                if file_age > (days_old * 24 * 3600):
                    image_file.unlink()
                    logger.info(f"Cleaned up old image: {image_file}")
                    
        except Exception as e:
            logger.error(f"Image cleanup error: {e}")