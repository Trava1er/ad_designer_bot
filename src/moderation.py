"""
AI-Powered Content Moderation Service for AdDesigner Hub Bot.
Uses advanced AI models for accurate and context-aware content moderation.
Optimized version with minimal code duplication.
"""

import logging
import json
from typing import Tuple, Optional, Dict
from openai import AsyncOpenAI
from bot_config import settings

logger = logging.getLogger(__name__)

# Configure OpenAI for moderation
client = AsyncOpenAI(api_key=settings.openai_api_key)


class ModerationPrompts:
    """Centralized storage for moderation prompts to avoid duplication."""
    
    # Policy rules (shared across all AI models)
    PROHIBITED_RULES = {
        'ru': [
            "Наркотики и психотропные вещества (любое упоминание, включая завуалированное)",
            "Оружие, боеприпасы, взрывчатка",
            "Порнография, интим-услуги, эскорт, проституция (даже с эвфемизмами)",
            "Азартные игры без лицензии",
            "Финансовые пирамиды, обещания гарантированного дохода (100%+, быстрые деньги)",
            "Мошенничество, обман, фальшивые документы, обналичивание",
            "Экстремизм, терроризм, призывы к насилию",
            "Взлом, кардинг, кража данных, нелегальные услуги",
            "Продажа персональных данных, баз данных",
            "Ненависть, дискриминация по любому признаку"
        ],
        'en': [
            "Drugs and psychotropic substances (any mention, including disguised)",
            "Weapons, ammunition, explosives",
            "Pornography, intimate services, escort, prostitution (even with euphemisms)",
            "Unlicensed gambling",
            "Financial pyramids, guaranteed income promises (100%+, quick money)",
            "Fraud, scams, fake documents, money laundering",
            "Extremism, terrorism, violence incitement",
            "Hacking, carding, data theft, illegal services",
            "Personal data sales, database sales",
            "Hate speech, discrimination of any kind"
        ]
    }
    
    ALLOWED_EXAMPLES = {
        'ru': [
            "Легальные услуги: дизайн, программирование, маркетинг, консультации",
            "Поиск работы и сотрудников",
            "Обучение и образовательные услуги",
            "Творческие услуги: фото, видео, музыка",
            "Ремонт, строительство, бытовые услуги",
            "Юридические консультации",
            "Фриланс и удаленная работа"
        ],
        'en': [
            "Legal services: design, programming, marketing, consulting",
            "Job search and hiring",
            "Education and training services",
            "Creative services: photo, video, music",
            "Repair, construction, household services",
            "Legal consultations",
            "Freelance and remote work"
        ]
    }
    
    VIOLATION_EXAMPLES = {
        'ru': [
            '"Легальные порошки" → наркотики',
            '"Финансовая помощь с гарантией 200%" → пирамида',
            '"Интимный массаж" → запрещенные услуги',
            '"Помогу обналичить" → мошенничество',
            '"Закладки, товар" → наркотики'
        ],
        'en': [
            '"Legal powders" → drugs',
            '"200% guaranteed profit" → pyramid scheme',
            '"Intimate massage" → prohibited services',
            '"Cash out help" → fraud'
        ]
    }
    
    @staticmethod
    def get_gpt4_prompt(language: str) -> str:
        """Generate GPT-4 system prompt based on language."""
        rules = ModerationPrompts.PROHIBITED_RULES.get(language, ModerationPrompts.PROHIBITED_RULES['en'])
        allowed = ModerationPrompts.ALLOWED_EXAMPLES.get(language, ModerationPrompts.ALLOWED_EXAMPLES['en'])
        
        if language == "ru":
            prompt = f"""Ты — эксперт по модерации контента для объявлений о работе и услугах в Telegram.

Твоя задача: ОЧЕНЬ СТРОГО проверить текст на нарушения законодательства РФ и политики Telegram.

ЗАПРЕЩЕНО (немедленный отказ):
{chr(10).join(f'{i+1}. {rule}' for i, rule in enumerate(rules))}

РАЗРЕШЕНО (если нет нарушений):
{chr(10).join(f'✅ {item}' for item in allowed)}

ВАЖНО:
- Анализируй СМЫСЛ и НАМЕРЕНИЯ, не только слова
- Обращай внимание на завуалированные предложения, эвфемизмы, сленг
- Отклоняй любые попытки обойти фильтры
- Ищи скрытые намеки

ФОРМАТ ОТВЕТА:
Если находишь ЛЮБОЕ нарушение:
VIOLATION: [категория]: [объяснение]

Если текст полностью легален:
APPROVED

Будь максимально строгим."""
        else:
            prompt = f"""You are an expert content moderator for job and service ads on Telegram.

Your task: VERY STRICTLY check the text for violations of laws and Telegram policy.

PROHIBITED (immediate rejection):
{chr(10).join(f'{i+1}. {rule}' for i, rule in enumerate(rules))}

ALLOWED (if no violations):
{chr(10).join(f'✅ {item}' for item in allowed)}

IMPORTANT:
- Analyze MEANING and INTENTIONS, not just words
- Look for disguised offers, euphemisms, slang
- Reject any attempts to bypass filters

RESPONSE FORMAT:
If you find ANY violation:
VIOLATION: [category]: [explanation]

If the text is completely legal:
APPROVED

Be extremely strict."""
        
        return prompt
    
    @staticmethod
    def get_gpt35_prompt(language: str, categories_list: str) -> str:
        """Generate GPT-3.5 system prompt based on language."""
        violations = ModerationPrompts.VIOLATION_EXAMPLES.get(language, ModerationPrompts.VIOLATION_EXAMPLES['en'])
        allowed = ModerationPrompts.ALLOWED_EXAMPLES.get(language, ModerationPrompts.ALLOWED_EXAMPLES['en'])
        
        if language == "ru":
            return f"""Ты — система автоматической модерации объявлений.

Проверь текст на соответствие следующим категориям запрещенного контента:

{categories_list}

ВАЖНО:
- Анализируй СМЫСЛ и КОНТЕКСТ, а не только слова
- Обращай внимание на завуалированные предложения
- Ищи скрытые намеки и эвфемизмы

Примеры нарушений:
{chr(10).join(f'❌ {example}' for example in violations)}

Примеры разрешенного контента:
{chr(10).join(f'✅ {example}' for example in allowed[:3])}

ФОРМАТ ОТВЕТА в JSON:
{{"approved": true}} - если безопасен
{{"approved": false, "category": "категория", "reason": "объяснение"}} - если нарушение

Будь очень строгим."""
        else:
            return f"""You are an automated ad moderation system.

Check the text against these prohibited content categories:

{categories_list}

IMPORTANT:
- Analyze MEANING and CONTEXT, not just words
- Look for disguised offers and euphemisms

Examples of violations:
{chr(10).join(f'❌ {example}' for example in violations)}

Examples of allowed content:
{chr(10).join(f'✅ {example}' for example in allowed[:3])}

RESPONSE FORMAT in JSON:
{{"approved": true}} - if safe
{{"approved": false, "category": "category", "reason": "explanation"}} - if violation

Be very strict."""


class ModerationService:
    """AI-powered content moderation service with multi-level AI checks."""
    
    # Policy categories for detailed analysis
    POLICY_CATEGORIES = {
        'ru': {
            'drugs': 'Наркотики, психотропные вещества',
            'weapons': 'Оружие, боеприпасы, взрывчатка',
            'fraud': 'Мошенничество, финансовые пирамиды',
            'adult': 'Порнография, интим-услуги',
            'gambling': 'Незаконные азартные игры',
            'extremism': 'Экстремизм, терроризм',
            'fake_docs': 'Поддельные документы',
            'personal_data': 'Продажа персональных данных',
            'hacking': 'Взлом, нелегальные услуги',
            'hate': 'Ненависть, дискриминация'
        },
        'en': {
            'drugs': 'Drugs, psychotropic substances',
            'weapons': 'Weapons, ammunition, explosives',
            'fraud': 'Fraud, financial pyramids',
            'adult': 'Pornography, intimate services',
            'gambling': 'Illegal gambling',
            'extremism': 'Extremism, terrorism',
            'fake_docs': 'Fake documents',
            'personal_data': 'Personal data sales',
            'hacking': 'Hacking, illegal services',
            'hate': 'Hate speech, discrimination'
        }
    }
    
    @staticmethod
    async def check_content(text: str, language: str = "ru") -> Tuple[bool, Optional[str]]:
        """
        AI-powered content moderation with three-stage analysis.
        
        Args:
            text: Text to check
            language: Content language (ru, en, zh-tw)
            
        Returns:
            Tuple of (is_approved, rejection_reason)
        """
        try:
            logger.info(f"[MODERATION] Starting moderation for: {text[:100]}...")
            
            # Run all 3 AI checks sequentially
            checks = [
                ("OpenAI API", ModerationService._check_openai_moderation(text)),
                ("GPT-4", ModerationService._check_gpt4_analysis(text, language)),
                ("GPT-3.5", ModerationService._check_policy_compliance(text, language))
            ]
            
            for stage_num, (stage_name, check_coro) in enumerate(checks, 1):
                logger.info(f"[MODERATION] Stage {stage_num}: {stage_name}")
                is_approved, reason = await check_coro
                
                if not is_approved:
                    logger.warning(f"[MODERATION] ❌ Rejected by {stage_name}: {reason}")
                    return (False, reason)
            
            # All checks passed
            logger.info(f"[MODERATION] ✅ APPROVED after all AI checks")
            return (True, None)
            
        except Exception as e:
            logger.error(f"[MODERATION] Critical error: {e}", exc_info=True)
            return (False, "Техническая ошибка модерации. Попробуйте позже.")
    
    @staticmethod
    async def _check_openai_moderation(text: str) -> Tuple[bool, Optional[str]]:
        """Stage 1: OpenAI Moderation API - Fast initial screening."""
        try:
            response = await client.moderations.create(input=text)
            
            if response.results and response.results[0].flagged:
                # Get flagged categories with scores
                result = response.results[0]
                violations = [
                    f"{cat} ({result.category_scores.__dict__[cat]:.2%})"
                    for cat, flagged in result.categories.__dict__.items()
                    if flagged and cat in result.category_scores.__dict__
                ]
                
                reason = f"Нарушение политики безопасности: {', '.join(violations)}"
                logger.warning(f"[MODERATION] OpenAI flagged: {violations}")
                return (False, reason)
            
            logger.info(f"[MODERATION] OpenAI: ✅ PASSED")
            return (True, None)
            
        except Exception as e:
            logger.error(f"[MODERATION] OpenAI API error: {e}")
            return (True, None)  # Don't block on API error
    
    @staticmethod
    async def _check_gpt4_analysis(text: str, language: str) -> Tuple[bool, Optional[str]]:
        """Stage 2: GPT-4 Deep Content Analysis - Context-aware understanding."""
        try:
            system_prompt = ModerationPrompts.get_gpt4_prompt(language)
            
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Проверь этот текст:\n\n{text}"}
                ],
                max_tokens=250,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"[MODERATION] GPT-4 response: {result}")
            
            if result.startswith("VIOLATION"):
                reason = result.replace("VIOLATION:", "").replace("VIOLATION", "").strip()
                return (False, f"❌ {reason or 'Обнаружено нарушение политики'}")
            
            if result.startswith("APPROVED"):
                logger.info(f"[MODERATION] GPT-4: ✅ APPROVED")
                return (True, None)
            
            # Unexpected response - reject for safety
            logger.warning(f"[MODERATION] GPT-4 unexpected: {result}")
            return (False, "Требуется ручная проверка.")
            
        except Exception as e:
            logger.error(f"[MODERATION] GPT-4 error: {e}")
            return (True, None)  # Don't block on error
    
    @staticmethod
    async def _check_policy_compliance(text: str, language: str) -> Tuple[bool, Optional[str]]:
        """Stage 3: GPT-3.5 Detailed Policy Compliance Check."""
        try:
            # Get policy categories
            categories = ModerationService.POLICY_CATEGORIES.get(language, ModerationService.POLICY_CATEGORIES['en'])
            categories_list = "\n".join(f"- {key}: {value}" for key, value in categories.items())
            
            system_prompt = ModerationPrompts.get_gpt35_prompt(language, categories_list)
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=200,
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"[MODERATION] GPT-3.5 response: {result_text}")
            
            # Parse JSON response
            try:
                result = json.loads(result_text)
                
                if not result.get("approved", True):
                    category = result.get("category", "unknown")
                    reason = result.get("reason", "Обнаружено нарушение")
                    logger.warning(f"[MODERATION] Policy violation: {category} - {reason}")
                    return (False, f"Запрещенный контент ({category}): {reason}")
                
                logger.info(f"[MODERATION] GPT-3.5: ✅ PASSED")
                return (True, None)
                
            except json.JSONDecodeError:
                logger.error(f"[MODERATION] Invalid JSON: {result_text}")
                return (True, None)  # Continue on parse error
            
        except Exception as e:
            logger.error(f"[MODERATION] GPT-3.5 error: {e}")
            return (True, None)  # Don't block on error
    
    @staticmethod
    async def check_image(image_url: str) -> Tuple[bool, Optional[str]]:
        """Check image content for violations using AI."""
        try:
            logger.info(f"[MODERATION] Image check: {image_url}")
            # Future: GPT-4 Vision implementation
            return (True, None)
        except Exception as e:
            logger.error(f"[MODERATION] Image error: {e}")
            return (False, "Техническая ошибка при проверке изображения")
    
    @staticmethod
    def get_moderation_stats() -> Dict:
        """Get moderation statistics (for admin panel)."""
        return {
            "total_checks": 0,
            "approved": 0,
            "rejected": 0,
            "ai_model": "GPT-4o-mini + GPT-3.5-turbo + OpenAI Moderation API"
        }


# Convenience instance
moderation_service = ModerationService()
