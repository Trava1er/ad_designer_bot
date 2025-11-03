# Визуальные карточки тарифов

## Требования к дизайну

### Формат изображений:
- **Размер:** 800x600px (оптимально для Telegram)
- **Формат:** PNG с прозрачностью или JPEG
- **Качество:** Высокое разрешение для читабельности

### Дизайн карточек:

#### 1. Тариф "Одно объявление" (single.png)
```
┌─────────────────────────────┐
│  🎯 ОДНО ОБЪЯВЛЕНИЕ         │
│                             │
│  ✓ 1 объявление             │
│  ✓ AI улучшение текста      │
│  ✓ Размещение в канале      │
│  ✓ Статистика показов       │
│                             │
│  💰 200₽ / $3 / 3 USDT      │
│                             │
│  [Выбрать тариф]            │
└─────────────────────────────┘
```

#### 2. Тариф "10 объявлений" (pack10.png)
```
┌─────────────────────────────┐
│  📦 10 ОБЪЯВЛЕНИЙ   🔥      │
│                             │
│  ✓ 10 объявлений            │
│  ✓ AI улучшение текста      │
│  ✓ Размещение в каналах     │
│  ✓ Приоритетная модерация   │
│  ✓ Расширенная статистика   │
│                             │
│  💰 800₽ / $12 / 12 USDT    │
│  ❌ 2000₽  💚 ЭКОНОМИЯ 60%  │
│                             │
│  [Выбрать тариф]            │
└─────────────────────────────┘
```

#### 3. Тариф "Безлимит" (unlimited.png)
```
┌─────────────────────────────┐
│  🏆 БЕЗЛИМИТ/МЕСЯЦ  ⭐      │
│                             │
│  ✓ Безлимит объявлений      │
│  ✓ AI улучшение текста      │
│  ✓ Приоритетное размещение  │
│  ✓ Персональный менеджер    │
│  ✓ Аналитика и отчеты       │
│  ✓ Эксклюзивные каналы      │
│                             │
│  💰 1500₽ / $22 / 22 USDT   │
│  ❌ 6000₽  💚 ЭКОНОМИЯ 75%  │
│                             │
│  [Выбрать тариф]            │
└─────────────────────────────┘
```

### Цветовая схема:
- **Основной:** #2B5278 (синий)
- **Акцент:** #FF6B6B (красный для скидок)
- **Успех:** #51CF66 (зеленый для экономии)
- **Текст:** #2C3E50 (темно-серый)
- **Фон:** #FFFFFF или градиент

### Шрифты:
- **Заголовки:** SF Pro Display Bold
- **Текст:** SF Pro Text Regular
- **Цены:** SF Pro Display Semibold

## Инструменты для создания:

### Вариант 1: Canva (быстро, без опыта)
1. Перейти на canva.com
2. Создать дизайн 800x600px
3. Использовать шаблоны "Pricing Card"
4. Экспортировать PNG

### Вариант 2: Figma (профессионально)
1. Создать фрейм 800x600
2. Добавить компоненты: заголовок, список, цена, кнопка
3. Применить стили и тени
4. Экспортировать PNG @2x

### Вариант 3: AI генерация (экспериментально)
Промпт для Midjourney/DALL-E:
```
Clean pricing card design for messaging app, 800x600px, 
modern minimalist style, blue and white colors, 
includes title, feature list with checkmarks, 
price in rubles/dollars/USDT, discount badge, 
professional business design, high contrast
```

## Интеграция в бота:

После создания изображений добавить в код:

### src/utils.py - функция отправки тарифа с изображением:

```python
async def send_tariff_card(message: Message, tariff_type: str, language: str):
    """Send visual tariff card with image."""
    from aiogram.types import FSInputFile
    
    tariff_images = {
        'single': 'images/tariffs/single.png',
        'pack10': 'images/tariffs/pack10.png',
        'unlimited': 'images/tariffs/unlimited.png'
    }
    
    image_path = tariff_images.get(tariff_type)
    if image_path and os.path.exists(image_path):
        photo = FSInputFile(image_path)
        caption = MessageLoader.get_message(f"tariffs.{tariff_type}_description", language)
        
        await message.answer_photo(
            photo=photo,
            caption=caption,
            reply_markup=get_tariff_selection_keyboard(language),
            parse_mode="HTML"
        )
    else:
        # Fallback to text
        await proceed_to_tariff_selection(message, language, state)
```

## TODO:
- [ ] Создать single.png (одно объявление)
- [ ] Создать pack10.png (10 объявлений)
- [ ] Создать unlimited.png (безлимит)
- [ ] Создать comparison.png (таблица сравнения всех тарифов)
- [ ] Интегрировать в src/handlers/payment.py
- [ ] Добавить анимацию/GIF версии (опционально)
