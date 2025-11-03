"""
Main entry point for AdDesigner Hub Telegram Bot.
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot_config import settings
from handlers import router
from utils import setup_logging, init_metrics
from database import init_db

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot."""
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        # Initialize metrics
        logger.info("Initializing metrics...")
        init_metrics(port=getattr(settings, 'metrics_port', 8000))
        
        # Initialize bot and dispatcher
        logger.info("Initializing bot...")
        bot = Bot(token=settings.telegram_bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Register router
        dp.include_router(router)
        
        logger.info("Bot configuration complete")
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())