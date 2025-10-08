import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN, LOG_FILE, LOG_LEVEL
from database import init_db, async_session
from handlers import start_router, portfolio_router, order_router
from sqlalchemy.ext.asyncio import AsyncSession

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

async def main():
    # Инициализация БД
    await init_db()

    # Создание бота и диспетчера
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Регистрация роутеров
    dp.include_router(start_router)
    dp.include_router(portfolio_router)
    dp.include_router(order_router)
    # Добавьте другие роутеры здесь

    # Middleware для сессии БД
    @dp.update.middleware
    async def db_session_middleware(handler, event, data):
        async with async_session() as session:
            data['session'] = session
            return await handler(event, data)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
