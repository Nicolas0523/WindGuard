from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from .config import settings
from .handlers import user


BOT_TOKEN = os.getenv("BOT_TOKEN") 
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(user)