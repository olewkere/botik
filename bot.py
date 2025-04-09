import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

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
if not WEBAPP_URL:
    logger.warning("Не знайдено WEBAPP_URL! Кнопка для відкриття WebApp не працюватиме.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає привітання та кнопку для відкриття Web App."""
    if not WEBAPP_URL:
         await update.message.reply_text("На жаль, URL веб-додатку не налаштовано.")
         return

    web_app_info = WebAppInfo(url=WEBAPP_URL)
    button = InlineKeyboardButton(text="🚀 Відкрити Планувальник", web_app=web_app_info)
    keyboard = InlineKeyboardMarkup([[button]])

    await update.message.reply_text(
        "Привіт! 👋 Натисни кнопку нижче, щоб відкрити свій планувальник завдань:",
        reply_markup=keyboard
    )

async def planner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє команду /planner, синонім /start."""
    await start(update, context)


def main() -> None:
    """Запускає бота."""
    logger.info("Запуск бота...")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("planner", planner))

    logger.info("Бот починає опитування...")
    application.run_polling()

if __name__ == "__main__":
    main()
