# AdDesigner Hub - Telegram Bot

A production-ready Telegram bot for managing paid advertisement submissions from designers with multi-language support, payment processing, AI-powered content generation, and admin moderation tools.

## Features

### Core Functionality
- 🎨 Designer advertisement submission and management
- 💰 Multi-currency payment processing (RUB, USD, USDT)
- 🤖 AI-powered text and image generation (OpenAI ChatGPT + DALL-E)
- 🌍 Multi-language support (Russian, English, Traditional Chinese)
- 📊 Admin moderation panel with analytics
- 📧 Automated PDF receipt generation
- 🔒 Secure webhook verification
- 📈 Comprehensive logging and monitoring

### Payment Providers
- **Yookassa** - Russian Ruble (RUB) payments
- **Stripe** - US Dollar (USD) payments  
- **NOWPayments** - USDT cryptocurrency payments

### AI Services
- **Text Generation** - Smart advertisement descriptions using ChatGPT
- **Image Generation** - DALL-E powered visuals with variations
- **Multi-language** - Localized prompts for different markets

## Project Structure

```
design_ads_bot/
├── config.py                  # Configuration management
├── bot.py                     # Main bot entry point
├── requirements.txt           # Python dependencies
├── db/
│   ├── __init__.py
│   ├── models.py             # SQLAlchemy database models
│   └── session.py            # Database session management
├── handlers/
│   ├── __init__.py
│   ├── user.py               # User interaction handlers
│   ├── admin.py              # Admin panel handlers
│   └── payments.py           # Payment processing handlers
├── services/
│   ├── __init__.py
│   ├── openai_text_service.py    # Text generation service
│   ├── openai_image_service.py   # Image generation service
│   └── payments/
│       ├── __init__.py
│       ├── base.py           # Abstract payment provider
│       ├── yookassa.py       # Yookassa implementation
│       ├── stripe_provider.py   # Stripe implementation
│       └── nowpayments.py    # NOWPayments implementation
├── utils/
│   ├── __init__.py
│   ├── localization.py       # Multi-language support
│   ├── receipt_generator.py  # PDF receipt generation
│   ├── logging.py            # Comprehensive logging
│   └── security.py           # Security utilities
├── locales/
│   ├── ru.yml                # Russian translations
│   ├── en.yml                # English translations
│   └── zh-tw.yml             # Traditional Chinese translations
├── static/
│   ├── receipts/             # Generated PDF receipts
│   └── images/               # AI-generated images
├── logs/                     # Application logs
├── migrations/               # Database migrations
└── docs/                     # Additional documentation
```

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root:

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_user_id

# Database
DATABASE_URL=sqlite:///bot.db
# For PostgreSQL: postgresql://user:password@localhost/dbname

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Payment Providers
YOOKASSA_ACCOUNT_ID=your_yookassa_account_id
YOOKASSA_SECRET_KEY=your_yookassa_secret_key

STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

NOWPAYMENTS_API_KEY=your_nowpayments_api_key

# Bot Configuration
DEFAULT_LANGUAGE=ru
SUPPORTED_LANGUAGES=ru,en,zh-tw
BOT_WEBHOOK_URL=https://yourdomain.com/webhook
BOT_WEBHOOK_SECRET=your_webhook_secret

# File Paths
RECEIPTS_DIR=static/receipts
IMAGES_DIR=static/images
LOGS_DIR=logs

# Business Settings
DEFAULT_AD_PRICE_RUB=1000
DEFAULT_AD_PRICE_USD=15
DEFAULT_AD_PRICE_USDT=15
AD_MODERATION_TIMEOUT_HOURS=24
MAX_AD_DESCRIPTION_LENGTH=500
MAX_IMAGE_VARIATIONS=3
```

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd design_ads_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from db.session import init_database; init_database()"
```

### 3. Running the Bot

```bash
# Development mode
python bot.py

# Production mode with PM2 (recommended)
pm2 start bot.py --name "ads-bot" --interpreter python3
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | Bot token from @BotFather |
| `ADMIN_ID` | ✅ | Telegram user ID of admin |
| `OPENAI_API_KEY` | ✅ | OpenAI API key for AI features |
| `DATABASE_URL` | ✅ | Database connection string |
| `YOOKASSA_ACCOUNT_ID` | ⚠️ | Required for RUB payments |
| `YOOKASSA_SECRET_KEY` | ⚠️ | Required for RUB payments |
| `STRIPE_SECRET_KEY` | ⚠️ | Required for USD payments |
| `NOWPAYMENTS_API_KEY` | ⚠️ | Required for USDT payments |

### Localization

The bot supports multiple languages with YAML-based translations in the `locales/` directory:

- `ru.yml` - Russian (default)
- `en.yml` - English
- `zh-tw.yml` - Traditional Chinese

Add new languages by creating additional YAML files and updating `SUPPORTED_LANGUAGES`.

## Database Models

### Core Models
- **User** - Bot users with preferences and subscription status
- **Ad** - Advertisement submissions with status tracking
- **Payment** - Payment transactions with provider details
- **Tariff** - Pricing plans for different markets
- **Subscription** - User subscription management
- **Channel** - Publication channels and targeting
- **Receipt** - Generated payment receipts
- **AdminAction** - Admin moderation audit trail
- **BotMetrics** - Bot usage analytics

## Payment Processing

### Supported Providers

1. **Yookassa (RUB)**
   - Russian market payments
   - Bank cards, wallets, etc.
   - Automatic webhook processing

2. **Stripe (USD)**
   - International credit cards
   - Secure payment processing
   - Real-time status updates

3. **NOWPayments (USDT)**
   - Cryptocurrency payments
   - USDT Tether support
   - Blockchain confirmation tracking

### Payment Flow

1. User selects advertisement package
2. Payment provider redirects to payment form
3. Webhook confirms payment completion
4. PDF receipt automatically generated
5. Advertisement approved for publication

## AI Integration

### Text Generation
- Smart advertisement descriptions
- Localized content for different markets
- Fallback templates for API failures
- Content moderation and filtering

### Image Generation
- DALL-E powered visuals
- Multiple style variations
- Local storage with CDN support
- Automatic resizing and optimization

## Security Features

- Webhook signature verification
- Rate limiting and spam protection
- Admin action audit logging
- Secure token storage
- Input validation and sanitization

## Monitoring & Logging

### Log Categories
- **Bot Operations** - User interactions, commands
- **Security Events** - Failed authentications, suspicious activity
- **Performance Metrics** - Response times, API calls
- **Payment Transactions** - Financial operations audit
- **Admin Actions** - Moderation decisions tracking

### Health Monitoring
- Database connection status
- External API availability
- Payment provider status
- Bot response times

## Deployment

### Production Checklist

1. ✅ Configure environment variables
2. ✅ Setup PostgreSQL database
3. ✅ Configure payment providers
4. ✅ Setup domain and SSL certificate
5. ✅ Configure webhook endpoints
6. ✅ Setup log rotation
7. ✅ Configure monitoring alerts
8. ✅ Setup backup procedures

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "bot.py"]
```

### PM2 Configuration

```json
{
  "name": "ads-bot",
  "script": "bot.py",
  "interpreter": "python3",
  "instances": 1,
  "autorestart": true,
  "watch": false,
  "max_memory_restart": "1G",
  "env": {
    "NODE_ENV": "production"
  }
}
```

## API Documentation

### Webhook Endpoints

- `POST /webhook/telegram` - Telegram bot updates
- `POST /webhook/yookassa` - Yookassa payment notifications
- `POST /webhook/stripe` - Stripe payment events
- `POST /webhook/nowpayments` - NOWPayments callbacks

### Admin API

- `GET /admin/stats` - Bot usage statistics
- `GET /admin/users` - User management
- `POST /admin/broadcast` - Mass message sending
- `GET /admin/payments` - Payment history

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For technical support or questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation in `docs/`

## Changelog

### v1.0.0 (Current)
- Initial release
- Multi-language support
- Payment processing
- AI integration
- Admin panel
- Comprehensive logging