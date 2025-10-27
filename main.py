from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import logging
import os

from handlers.userm import router as user_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Загрузка токена
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("Не найден BOT_TOKEN в .env файле")
    raise ValueError("Не найден BOT_TOKEN в .env файле")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключение роутеров
dp.include_router(user_router)

# Запуск
if __name__ == '__main__':
    logger.info("Запуск бота братуфан")
    dp.run_polling(bot, skip_updates=True)