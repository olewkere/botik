# bot.py
import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes # Прибираємо MessageHandler, filters

# Завантажуємо змінні середовища
load_dotenv()

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL')

if not BOT_TOKEN:
    logger.error("Не знайдено BOT_TOKEN! Перевір змінні середовища.")
    exit()
# Не виходимо, якщо немає WEBAPP_URL, просто логуємо попередження
if not WEBAPP_URL:
    logger.warning("Не знайдено WEBAPP_URL! Кнопка для відкриття WebApp не працюватиме.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає привітання та кнопку для відкриття Web App."""
    if not WEBAPP_URL:
         await update.message.reply_text("На жаль, URL веб-додатку не налаштовано.")
         return

    # Створюємо інформацію про Web App
    web_app_info = WebAppInfo(url=WEBAPP_URL)
    # Створюємо кнопку, яка відкриває Web App
    button = InlineKeyboardButton(text="🚀 Відкрити Планувальник", web_app=web_app_info)
    keyboard = InlineKeyboardMarkup([[button]])

    await update.message.reply_text(
        "Привіт! 👋 Натисни кнопку нижче, щоб відкрити свій планувальник завдань:",
        reply_markup=keyboard
    )

async def planner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє команду /planner, синонім /start."""
    await start(update, context)

# Прибираємо web_app_data_handler, бо він більше не потрібен

def main() -> None:
    """Запускає бота."""
    logger.info("Запуск бота...")

    # Створюємо додаток та передаємо токен
    application = Application.builder().token(BOT_TOKEN).build()

    # Реєструємо обробники команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("planner", planner))
    # Прибираємо реєстрацію MessageHandler для WEB_APP_DATA

    # Запускаємо бота в режимі опитування (polling)
    logger.info("Бот починає опитування...")
    # Можна повернути Update.ALL_TYPES або прибрати allowed_updates, якщо не потрібні специфічні типи
    application.run_polling() # allowed_updates=Update.ALL_TYPES

if __name__ == "__main__":
    main()
