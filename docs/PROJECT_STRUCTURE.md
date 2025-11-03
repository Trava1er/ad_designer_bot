# Структура проекта

## Основные директории

```
design_ads_bot/
├── src/                      # Исходный код бота
│   ├── handlers/            # Обработчики команд и событий
│   ├── main.py             # Точка входа приложения
│   ├── bot_config.py       # Конфигурация бота
│   ├── database.py         # Модели базы данных
│   ├── services.py         # Бизнес-логика (AI, каналы)
│   ├── utils.py            # Утилиты (клавиатуры, локализация)
│   ├── moderation.py       # Модерация контента
│   └── progress_bar.py     # Индикаторы прогресса
│
├── locales/                 # Локализация (YAML)
│   ├── ru.yml              # Русский язык
│   ├── en.yml              # Английский язык
│   └── zh-tw.yml           # Китайский язык
│
├── webapp/                  # Web приложение (Telegram Web App)
│   ├── tariffs_new.html    # Страница выбора тарифов (темная тема)
│   └── README.md           # Документация Web App
│
├── data/                    # Конфигурационные файлы
│   ├── keyboards.json      # Клавиатуры (устаревает, переход на utils.py)
│   └── messages.json       # Сообщения (устаревает, используются locales/*.yml)
│
├── docs/                    # Документация
│   ├── QUICK_CREATE_MODE.md        # Быстрое создание объявлений
│   ├── UX_ANALYSIS_REPORT.md       # Анализ UX
│   ├── WEBAPP_INTEGRATION.md       # Интеграция Web App
│   └── archive/                    # Архив документов
│       ├── CHANGES_LOG.md          # История изменений
│       └── UX_IMPROVEMENTS_PLAN.md # План улучшений UX
│
├── scripts/                 # Вспомогательные скрипты
│   ├── check_localization.py       # Проверка локализации
│   └── generate_comparison_cards.py # Генерация карточек тарифов
│
├── migrations/              # Миграции базы данных
│   └── archive/            # Выполненные миграции
│
├── images/                  # Статические изображения
│   └── tariffs/            # Изображения тарифов
│
└── logs/                    # Логи приложения
    ├── bot.log             # Общие логи бота
    ├── bot.pid             # PID запущенного процесса
    ├── security.log        # Логи безопасности
    └── webhook.log         # Логи webhook

```

## Файлы запуска

- `start.sh` - Запуск бота
- `stop.sh` - Остановка бота
- `restart.sh` - Перезапуск бота

## Конфигурация

- `.env` - Переменные окружения (секреты, токены)
- `.env.example` - Пример файла конфигурации
- `requirements.txt` - Зависимости Python
- `Dockerfile` - Конфигурация Docker
- `docker-compose.yml` - Оркестрация контейнеров

## База данных

- `bot.db` - SQLite база данных
- Модели: `User`, `Ad`, `Payment`
- Миграции: `migrations/archive/`

## Web App

URL: https://trava1er.github.io/ad_designer_bot/tariffs_new.html

Функционал:
- Выбор тарифного плана (разовый/подписка)
- Выбор валюты (RUB/USD/USDT)
- Выбор способа оплаты (карта/крипто/Telegram Stars)
- Темная тема оформления
- Интеграция с ботом через Web App API

## Архитектура

### Обработчики (src/handlers/)
- `user.py` - Основные команды пользователя
- `webapp.py` - Обработка Web App данных
- `admin.py` - Административные команды

### Сервисы (src/services.py)
- `AIService` - Улучшение текстов через AI
- `ChannelService` - Публикация в каналы
- `PaymentService` - Обработка платежей

### Утилиты (src/utils.py)
- `MessageLoader` - Загрузка локализованных сообщений
- Генераторы клавиатур
- Валидация и форматирование

## Локализация

Все сообщения хранятся в `locales/*.yml`:
- Поддержка 3 языков: RU, EN, ZH-TW
- YAML формат для удобства редактирования
- Промпты для AI включены в локали

## CI/CD

- GitHub Pages для Web App
- Docker для деплоя
- Скрипты для автоматизации

## Очищено

Удалены следующие дубликаты и временные файлы:
- `db_old/`, `services_old/`, `utils_old/` - старые версии модулей
- `bot.py`, `main.py`, `config.py` - дубликаты из корня
- `*.bak` - резервные копии
- `*.log` - логи перемещены в logs/
- `__pycache__/` - кеш Python
- `.dependencies_installed` - флаг установки зависимостей
- `bot.db-shm`, `bot.db-wal` - временные файлы SQLite
- `webapp/tariffs.html` - старая версия Web App
- `restructure.sh` - временный скрипт
