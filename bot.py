"""
AdDesigner Hub - Main bot entry point.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from utils.logging import setup_logging, bot_logger
from db.session import init_database
from utils.localization import localization

# Import handlers
# from handlers.user import user_router
# from handlers.admin import admin_router  
# from handlers.payments import payments_router

logger = logging.getLogger(__name__)


async def on_startup():
    """Initialize bot on startup."""
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_database()
        
        # Load localization
        logger.info("Loading localization...")
        localization.reload_translations()
        
        logger.info("Bot startup completed successfully")
        bot_logger.log_user_action(settings.admin_id, "bot_started")
        
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        raise


async def on_shutdown():
    """Cleanup on bot shutdown."""
    logger.info("Bot shutting down...")
    bot_logger.log_user_action(settings.admin_id, "bot_stopped")


async def main():
    """Main bot function."""
    # Setup logging
    setup_logging()
    logger.info("Starting AdDesigner Hub bot...")
    
    # Validate configuration
    if not settings.telegram_bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not provided")
        return
    
    if not settings.admin_id:
        logger.error("ADMIN_ID not provided")
        return
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register startup/shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Register routers
    # dp.include_router(user_router)
    # dp.include_router(admin_router)
    # dp.include_router(payments_router)
    
    try:
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    """Run the bot."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise