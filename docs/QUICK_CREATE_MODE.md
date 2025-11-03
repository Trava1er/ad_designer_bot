# Quick Create Mode Implementation Plan

## Концепция
Режим быстрого создания: пользователь отправляет текст + фото одним сообщением, AI автоматически улучшает, показывается результат, затем выбор тарифа и оплата.

## Текущий flow (медленный)
1. Нажать "Создать объявление"
2. Выбрать "Текст"
3. Отправить текст
4. Выбрать "С AI" или "Без AI"
5. Если AI - подтвердить результат
6. Выбрать валюту
7. Выбрать тариф
8. Оплатить

**Проблема:** 8 шагов, много кликов

## Новый flow (быстрый)
1. Отправить текст (или текст + фото)
2. Бот автоматически улучшает с AI
3. Показать результат (кнопка "Продолжить" / "Редактировать")
4. Выбор тарифа
5. Оплата

**Результат:** 5 шагов, -37% времени

## Реализация

### Добавить кнопку в главное меню

#### keyboards.json
```json
"main_menu": {
  "ru": [
    ["📝 Создать объявление"],
    ["⚡ Быстрое создание"],  // <- NEW
    ["💼 Мои объявления", "ℹ️ Помощь"]
  ],
  "en": [
    ["📝 Create Ad"],
    ["⚡ Quick Create"],  // <- NEW
    ["💼 My Ads", "ℹ️ Help"]
  ],
  "zh-tw": [
    ["📝 建立廣告"],
    ["⚡ 快速建立"],  // <- NEW
    ["💼 我的廣告", "ℹ️ 幫助"]
  ]
}
```

### Добавить локализацию

#### locales/ru.yml
```yaml
quick_create:
  welcome: |
    ⚡ <b>Режим быстрого создания</b>
    
    Просто отправьте текст вашего объявления.
    Можете добавить фото - просто прикрепите его к сообщению.
    
    AI автоматически улучшит ваш текст!
    
  processing: |
    ⚡ Обрабатываю с AI...
    Это займет ~10 секунд
    
  result: |
    ✨ <b>Готово! Вот ваше объявление:</b>
    
    {improved_text}
    
    💡 AI автоматически:
    • Сделал текст более убедительным
    • Исправил ошибки
    • Добавил призыв к действию
    
  continue_prompt: |
    Продолжить с этим текстом?
```

### Создать новый обработчик

#### src/handlers/quick_create.py
```python
"""Quick create mode - fast ad creation with auto AI improvement."""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils import (
    MessageLoader, KeyboardLoader, UserStates,
    get_user_info_from_message, process_ai_improvement,
    proceed_to_currency_selection
)
from database import get_db_session, get_or_create_user
from services import ai_service

router = Router()


@router.message(F.text.in_(KeyboardLoader.get_button_texts_all_langs("main_menu", (1, 0))))
async def start_quick_create(message: Message, state: FSMContext):
    """Start quick create mode."""
    user, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user:
        return
    
    welcome_text = MessageLoader.get_message("quick_create.welcome", language)
    
    await message.answer(welcome_text, parse_mode="HTML")
    await state.set_state(UserStates.quick_create_waiting_content)


@router.message(UserStates.quick_create_waiting_content)
async def process_quick_create(message: Message, state: FSMContext):
    """Process quick create content with auto AI improvement."""
    user, language = await get_user_info_from_message(message, get_db_session, get_or_create_user)
    if not user:
        return
    
    # Extract text
    text = message.text or message.caption or ""
    
    if not text:
        error_text = MessageLoader.get_message("errors.no_text", language)
        await message.answer(error_text)
        return
    
    # Save original text and photo if present
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    
    # Show processing message
    processing_text = MessageLoader.get_message("quick_create.processing", language)
    processing_msg = await message.answer(processing_text)
    
    try:
        # Auto-improve with AI
        improved_text = await process_ai_improvement(ai_service, text, language)
        
        if not improved_text:
            improved_text = text  # Fallback to original
        
        # Save to state
        await state.update_data(
            ad_text=improved_text,
            original_text=text,
            photo_file_id=photo_file_id
        )
        
        # Delete processing message
        try:
            await processing_msg.delete()
        except:
            pass
        
        # Show result
        result_text = MessageLoader.get_message(
            "quick_create.result",
            language,
            improved_text=improved_text
        )
        
        # Send with photo if available
        if photo_file_id:
            await message.answer_photo(
                photo=photo_file_id,
                caption=result_text,
                parse_mode="HTML"
            )
        else:
            await message.answer(result_text, parse_mode="HTML")
        
        # Prompt to continue
        continue_text = MessageLoader.get_message("quick_create.continue_prompt", language)
        
        # Simple inline keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Продолжить", callback_data="qc_continue"),
                InlineKeyboardButton(text="✏️ Редактировать", callback_data="qc_edit")
            ],
            [InlineKeyboardButton(text="👁 Показать изменения", callback_data="qc_compare")]
        ])
        
        await message.answer(continue_text, reply_markup=keyboard)
        await state.set_state(UserStates.quick_create_confirm)
        
    except Exception as e:
        logger.error(f"Quick create error: {e}")
        try:
            await processing_msg.delete()
        except:
            pass
        
        error_text = MessageLoader.get_message("errors.processing_error", language)
        await message.answer(error_text)
        await state.clear()


@router.callback_query(F.data == "qc_continue")
async def quick_create_continue(callback: CallbackQuery, state: FSMContext):
    """Continue to tariff selection."""
    user, language = await get_user_info_from_message(callback.message, get_db_session, get_or_create_user)
    if not user:
        return
    
    await callback.answer()
    
    # Proceed to currency selection
    await proceed_to_currency_selection(callback.message, language, state)


@router.callback_query(F.data == "qc_edit")
async def quick_create_edit(callback: CallbackQuery, state: FSMContext):
    """Allow editing."""
    user, language = await get_user_info_from_message(callback.message, get_db_session, get_or_create_user)
    if not user:
        return
    
    await callback.answer()
    
    data = await state.get_data()
    current_text = data.get("ad_text", "")
    
    edit_text = MessageLoader.get_message("ad_creation.edit_instruction", language)
    await callback.message.answer(edit_text, parse_mode="HTML")
    await callback.message.answer(f"```\n{current_text}\n```", parse_mode="Markdown")
    
    await state.set_state(UserStates.quick_create_waiting_content)


@router.callback_query(F.data == "qc_compare")
async def quick_create_compare(callback: CallbackQuery, state: FSMContext):
    """Show comparison."""
    user, language = await get_user_info_from_message(callback.message, get_db_session, get_or_create_user)
    if not user:
        return
    
    await callback.answer()
    
    data = await state.get_data()
    original = data.get("original_text", "")
    improved = data.get("ad_text", "")
    
    comparison_text = MessageLoader.get_message(
        "ai_comparison",
        language,
        original_text=original,
        improved_text=improved,
        original_length=len(original),
        improved_length=len(improved)
    )
    
    await callback.message.answer(comparison_text, parse_mode="HTML")
```

### Добавить состояние в UserStates

#### src/utils.py
```python
class UserStates(StatesGroup):
    # ... existing states ...
    quick_create_waiting_content = State()
    quick_create_confirm = State()
```

### Зарегистрировать роутер

#### main.py
```python
from handlers import quick_create

# ...

dp.include_router(quick_create.router)
```

## Метрики для отслеживания

- Использование быстрого создания vs обычного
- Время до первого созданного объявления
- Conversion rate (старт → оплата)

**Ожидаемое улучшение:**
- -40% времени создания
- +60% использование AI (автоматически)
- +25% конверсия (меньше шагов)

## Тестирование

1. Нажать "⚡ Быстрое создание"
2. Отправить текст: "Дизайн логотипа 3000р"
3. Проверить AI улучшение
4. Нажать "Продолжить"
5. Выбрать валюту и тариф
6. Оплатить

## Оценка времени
- Добавить кнопку: 5 мин
- Локализация: 15 мин
- Создать обработчик: 2 часа
- Тестирование: 30 мин
- **Итого: ~3 часа**

## Приоритет
**СРЕДНИЙ** - Удобно, но не критично. Основной flow работает.
