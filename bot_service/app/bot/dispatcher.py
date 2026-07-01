from aiogram import Bot, Dispatcher
from app.bot.handlers import router
from app.core.config import settings

# создаём bot и dispatcher для подключения handlers
bot = Bot(token=settings.telegram_bot_token)
dispatcher = Dispatcher()
dispatcher.include_router(router)