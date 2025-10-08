import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройки бота
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Токен бота от BotFather
CHANNEL_ID = os.getenv('CHANNEL_ID')  # ID канала, например '@username' или -100xxxxxxxxxx для приватного
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))  # ID администратора

# Настройки базы данных
DATABASE_URL = 'sqlite+aiosqlite:///db.sqlite'  # SQLite база данных

# Настройки логирования
LOG_FILE = 'bot.log'
LOG_LEVEL = 'INFO'

# Настройки OpenAI (опционально)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Ключ для OpenAI, если используется

# Другие константы
PAYMENT_CARDS = {
    'sber': '1234-5678-9012-3456',  # Замени на реальные
    'tinkoff': '9876-5432-1098-7654'
}

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")
if not CHANNEL_ID:
    raise ValueError("CHANNEL_ID не найден в .env файле")
if ADMIN_ID == 0:
    raise ValueError("ADMIN_ID не найден в .env файле")
