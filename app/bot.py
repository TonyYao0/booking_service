import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession

from app.handlers import start, booking

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в .env")

# ============================================================
# НАСТРОЙКА ПРОКСИ
# ============================================================


PROXY_LOGIN = "BeU7M8uOh1gv"
PROXY_PASSWORD = "Fd741ItTArbsWjne"
PROXY_HOST = "pool.proxy.market"
PROXY_PORT = "10000"

PROXY_URL = f"http://{PROXY_LOGIN}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}"

print(f">>> Прокси: {PROXY_HOST}:{PROXY_PORT}")

session = AiohttpSession(proxy=PROXY_URL)
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    session=session,
)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(start.router)
dp.include_router(booking.router)