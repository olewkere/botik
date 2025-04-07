# bot.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import os # Потрібен для отримання WEBAPP_URL в start

# Базове логування для функцій обробників
logger = logging.getLogger(__name__)

# Змінну WEBAPP_URL тепер будемо отримувати з основного додатку або os.getenv
# Краще передавати її через context або отримувати напряму тут

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Надсилає привітання та кнопку для відкриття Web App."""
    # Отримуємо URL з context.bot_data або напряму з env
    WEBAPP_URL = context.bot_data.get('webapp_url') # Отримуємо з контексту
    if not WEBAPP_URL:
         # Спробуємо отримати з env як запасний варіант
         WEBAPP_URL = os.getenv('WEBAPP_URL')
         if not WEBAPP_URL:
              logger.warning("WEBAPP_URL не знайдено ні в context, ні в env для команди start")
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
