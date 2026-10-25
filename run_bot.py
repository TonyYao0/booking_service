import asyncio
import logging

from app.bot import bot, dp


async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Бот запущен (polling). Ctrl+C для остановки.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())