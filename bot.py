# bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import os # Потрібен для отримання WEBAPP_URL в start

# Базове логування для функцій обробників
logger = logging.getLogger(__name__)

# Змінну WEBAPP_URL тепер будемо отримувати з основного додатку або os.getenv
# Краще передавати її через context або отримувати напряму тут

# bot.py

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає привітання та кнопку для відкриття Web App."""
    logger.info(f"===== Команда /start або /planner отримана від користувача {update.effective_user.id} =====") # Більш помітний лог
    WEBAPP_URL = context.bot_data.get('webapp_url')
    logger.info(f"Спроба отримати WEBAPP_URL з context.bot_data. Результат: {WEBAPP_URL}") # Логуємо результат з контексту

    if not WEBAPP_URL:
         WEBAPP_URL = os.getenv('WEBAPP_URL')
         logger.info(f"WEBAPP_URL не знайдено в context. Спроба отримати з os.getenv. Результат: {WEBAPP_URL}") # Логуємо результат з env

    if not WEBAPP_URL:
         logger.error("!!! WEBAPP_URL не вдалося отримати ні з context, ні з env. Команда start не може створити кнопку.") # Помітний лог помилки
         await update.message.reply_text("На жаль, URL веб-додатку не налаштовано.")
         return

    logger.info(f"WEBAPP_URL '{WEBAPP_URL}' буде використано для створення кнопки.")
    web_app_info = WebAppInfo(url=WEBAPP_URL)
    button = InlineKeyboardButton(
        text="🚀 Відкрити Планувальник",
        web_app=web_app_info
    )
    keyboard = InlineKeyboardMarkup([[button]])

    await update.message.reply_text(
        "Привіт! 👋 Натисни кнопку нижче, щоб відкрити свій планувальник завдань:",
        reply_markup=keyboard
    )
    logger.info(f"Повідомлення з кнопкою WebApp надіслано користувачу {update.effective_user.id}")

async def planner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Синонім /start."""
    await start(update, context)


async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє дані, отримані від Web App."""
    user = update.effective_user
    received_text = update.message.web_app_data.data
    logger.info(f"Отримано дані Web App від {user.username} (ID: {user.id}): {len(received_text)} символів")

    if received_text:
        await context.bot.send_message(
            chat_id=user.id,
            text="📋 Ваш список завдань для поширення:\n(Можете переслати це повідомлення forward)"
        )
        await context.bot.send_message(chat_id=user.id, text=received_text)
    else:
         await context.bot.send_message(chat_id=user.id, text="Отримано порожні дані від Web App.")
