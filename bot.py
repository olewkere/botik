# bot.py
import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

# Завантажуємо змінні середовища
load_dotenv()

# Налаштування логування (корисно для дебагу на сервері)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING) # Щоб зменшити спам від httpx
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL')

if not BOT_TOKEN:
    logger.error("Не знайдено BOT_TOKEN! Перевір змінні середовища.")
    exit()
if not WEBAPP_URL:
    logger.error("Не знайдено WEBAPP_URL! Перевір змінні середовища.")
    # Можна не виходити, але кнопка не працюватиме
    # exit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає привітання та кнопку для відкриття Web App."""
    if not WEBAPP_URL:
         await update.message.reply_text("На жаль, URL веб-додатку не налаштовано.")
         return

    # Створюємо інформацію про Web App
    web_app_info = WebAppInfo(url=WEBAPP_URL)

    # Створюємо кнопку, яка відкриває Web App
    button = InlineKeyboardButton(
        text="🚀 Відкрити Планувальник",
        web_app=web_app_info
    )
    # Створюємо клавіатуру з однією кнопкою
    keyboard = InlineKeyboardMarkup([[button]])

    await update.message.reply_text(
        "Привіт! 👋 Натисни кнопку нижче, щоб відкрити свій планувальник завдань:",
        reply_markup=keyboard
    )

async def planner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє команду /planner, яка є синонімом /start для зручності."""
    await start(update, context)


def main() -> None:
    """Запускає бота."""
    logger.info("Запуск бота...")

    # Створюємо додаток та передаємо токен
    application = Application.builder().token(BOT_TOKEN).build()

    # Реєструємо обробники команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("planner", planner)) # Додаткова команда

    # Запускаємо бота в режимі опитування (polling)
    logger.info("Бот починає опитування...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
