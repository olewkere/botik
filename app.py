import os
import threading
import logging
import asyncio
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from functools import wraps
from models import db, User, Task
from werkzeug.exceptions import NotFound
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import bot as bot_handlers

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
db_user = os.getenv('DATABASE_USER')
db_password = os.getenv('DATABASE_PASSWORD')
db_host = os.getenv('DATABASE_HOST')
db_name = os.getenv('DATABASE_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

@app.context_processor
def inject_current_year():
    """Робить поточний рік доступним для всіх шаблонів."""
    return {'current_year': datetime.utcnow().year}

db.init_app(app)


with app.app_context():
    try:
        print("Спроба створити/оновити таблиці бази даних...")
        db.create_all()
        print("Таблиці успішно створено/оновлено (або вже існували).")
    except Exception as e:
        print(f"Помилка при створенні/оновленні таблиць: {e}")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


CATEGORIES = {
    'spring': 'Весна 🌱',
    'summer': 'Літо ☀️',
    'autumn': 'Осінь 🍂',
    'winter': 'Зима ❄️',
    'general': 'Загальні 📌'
}


@app.route('/')
def index():
    """Головна сторінка: перенаправляє на планувальник, якщо увійшов, інакше на логін."""
    if 'user_id' in session:
        return redirect(url_for('planner'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Сторінка та обробка реєстрації."""
    if 'user_id' in session:
        return redirect(url_for('planner'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if not username or not password or not password_confirm:
            flash('Будь ласка, заповніть усі поля.', 'error')
            return render_template('register.html')

        if password != password_confirm:
            flash('Паролі не співпадають.', 'error')
            return render_template('register.html')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Це ім\'я користувача вже зайняте.', 'error')
            return render_template('register.html')

        new_user = User(username=username)
        new_user.set_password(password)
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка реєстрації: {e}', 'error')
            print(f"Помилка при реєстрації: {e}")
            return render_template('register.html')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Сторінка та обробка входу."""
    if 'user_id' in session:
        return redirect(url_for('planner'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Будь ласка, введіть ім\'я користувача та пароль.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Привіт, {user.username}! Вхід успішний!', 'success')
            return redirect(url_for('planner'))
        else:
            flash('Неправильне ім\'я користувача або пароль.', 'error')
            return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Вихід користувача."""
    username = session.get('username', 'Користувач')
    session.pop('user_id', None)
    session.pop('username', None)
    flash(f'До побачення, {username}! Ви успішно вийшли.', 'info')
    return redirect(url_for('login'))


@app.route('/planner')
@login_required
def planner():
    """Відображає сторінку планувальника з завданнями користувача."""
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.category, Task.timestamp.desc()).all()

    tasks_by_category = {category_key: [] for category_key in CATEGORIES.keys()}
    for task in tasks:
        if task.category in tasks_by_category:
            tasks_by_category[task.category].append(task)
        else:
            tasks_by_category['general'].append(task)

    return render_template('planner.html', tasks_by_category=tasks_by_category, categories=CATEGORIES)


@app.route('/add_task', methods=['POST'])
@login_required
def add_task():
    """Додає нове завдання."""
    content = request.form.get('content')
    category = request.form.get('category')

    if not content:
        flash('Текст завдання не може бути порожнім!', 'error')
        return redirect(url_for('planner'))

    if category not in CATEGORIES:
        flash('Невірна категорія!', 'error')
        category = 'general'

    new_task = Task(content=content, category=category, user_id=session['user_id'])
    try:
        db.session.add(new_task)
        db.session.commit()
        flash('Завдання успішно додано!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Не вдалося додати завдання: {e}', 'error')
        print(f"Помилка додавання завдання: {e}")

    return redirect(url_for('planner'))


@app.route('/toggle_task/<int:task_id>', methods=['POST'])
@login_required
def toggle_task(task_id):
    """Відмічає завдання як виконане/невиконане."""
    task = Task.query.get_or_404(task_id)
    
    if task.user_id != session['user_id']:
        flash('У вас немає доступу до цього завдання.', 'danger')
        return redirect(url_for('planner'))

    task.is_completed = not task.is_completed
    try:
        db.session.commit()
        status = "виконано" if task.is_completed else "не виконано"
        flash(f'Статус завдання "{task.content[:20]}..." змінено на "{status}".', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Не вдалося змінити статус завдання: {e}', 'error')
        print(f"Помилка зміни статусу завдання: {e}")

    return redirect(url_for('planner'))


@app.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    """Видаляє завдання."""
    task = Task.query.get_or_404(task_id)

    if task.user_id != session['user_id']:
        flash('У вас немає доступу до цього завдання.', 'danger')
        return redirect(url_for('planner'))

    try:
        content_preview = task.content[:20]
        db.session.delete(task)
        db.session.commit()
        flash(f'Завдання "{content_preview}..." успішно видалено.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Не вдалося видалити завдання: {e}', 'error')
        print(f"Помилка видалення завдання: {e}")

    return redirect(url_for('planner'))


@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    """Редагує існуюче завдання (GET - показати форму, POST - зберегти зміни)."""
    task = Task.query.get_or_404(task_id)

    if task.user_id != session['user_id']:
        flash('У вас немає доступу до редагування цього завдання.', 'danger')
        return redirect(url_for('planner'))

    if request.method == 'POST':
        new_content = request.form.get('content')
        new_category = request.form.get('category')

        if not new_content:
            flash('Текст завдання не може бути порожнім!', 'error')
            return render_template('edit_task.html', task=task, categories=CATEGORIES)

        if new_category not in CATEGORIES:
             flash('Невірна категорія!', 'error')
             new_category = task.category

        task.content = new_content
        task.category = new_category
        try:
            db.session.commit()
            flash('Завдання успішно оновлено!', 'success')
            return redirect(url_for('planner'))
        except Exception as e:
            db.session.rollback()
            flash(f'Не вдалося оновити завдання: {e}', 'error')
            print(f"Помилка оновлення завдання: {e}")
            return render_template('edit_task.html', task=task, categories=CATEGORIES)

    return render_template('edit_task.html', task=task, categories=CATEGORIES)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# --- Логіка запуску Telegram Бота ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL') # Потрібен для кнопки

if not BOT_TOKEN:
    logger.warning("BOT_TOKEN не знайдено! Telegram бот не буде запущено.")
    bot_application = None
else:
    logger.info("Налаштування Telegram бота...")
    bot_builder = Application.builder().token(BOT_TOKEN)
    bot_application = bot_builder.build()

    if WEBAPP_URL:
        bot_application.bot_data['webapp_url'] = WEBAPP_URL
        logger.info(f"Додано webapp_url ({WEBAPP_URL}) до bot_data.")
    else:
         logger.warning("WEBAPP_URL не встановлено. Кнопка WebApp може не працювати.")

    logger.info("Реєстрація обробників команд...")
    bot_application.add_handler(CommandHandler("start", bot_handlers.start))
    bot_application.add_handler(CommandHandler("planner", bot_handlers.planner))
    logger.info("Реєстрація обробника WebApp даних...")
    bot_application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, bot_handlers.web_app_data_handler))

    # ! ОНОВЛЕНА ФУНКЦІЯ ДЛЯ ПОТОКУ !
    def run_bot_polling():
        """Функція для запуску polling у потоці з власним event loop."""
        thread_name = threading.current_thread().name # Отримуємо ім'я потоку для логів
        logger.info(f"Налаштування event loop для потоку '{thread_name}'...")
        # Створюємо новий event loop для цього потоку
        loop = asyncio.new_event_loop()
        # Встановлюємо цей loop як поточний для цього потоку
        asyncio.set_event_loop(loop)
        logger.info(f"Event loop створено та встановлено для потоку '{thread_name}'.")

        logger.info(f"Запуск Telegram Bot Polling у потоці '{thread_name}'...")
        try:
            # Тепер run_polling має знайти event loop у цьому потоці
            # run_polling сам подбає про запуск та роботу loop всередині
            bot_application.run_polling(allowed_updates=Update.ALL_TYPES)
            logger.info(f"Telegram Bot Polling коректно зупинено в потоці '{thread_name}'.")
        except Exception as e:
            # Логуємо будь-які помилки, що виникають під час роботи polling
            logger.error(f"Помилка під час роботи polling у потоці Telegram бота ('{thread_name}'): {e}", exc_info=True)
        finally:
            # Коли run_polling завершується (наприклад, при зупинці програми),
            # намагаємось закрити loop, хоча для daemon потоку це може не виконатись.
            try:
                if loop.is_running():
                    logger.info(f"Зупинка event loop для потоку '{thread_name}'.")
                    loop.stop()
                logger.info(f"Закриття event loop для потоку '{thread_name}'.")
                loop.close()
            except Exception as e:
                logger.error(f"Помилка при закритті event loop у потоці '{thread_name}': {e}", exc_info=True)


    # Створюємо та запускаємо потік для бота (додаємо ім'я для ясності в логах)
    bot_thread = threading.Thread(target=run_bot_polling, name="TelegramBotThread", daemon=True)
    bot_thread.start()
    logger.info(f"Потік для Telegram бота запущено: {bot_thread.name}")

# --- Запуск Flask (тільки для локальної розробки, Gunicorn це ігнорує) ---
if __name__ == '__main__':
    # При локальному запуску `python app.py` Flask запуститься,
    # а потік з ботом вже буде працювати паралельно.
    logger.info("Запуск Flask development server...")
    # debug=True перезапускає додаток при змінах, що може перезапускати потік бота
    # Краще вимкнути debug=True при тестуванні спільної роботи
    app.run(debug=False, host='0.0.0.0', port=5000) # Використовуємо інший порт, якщо 5000 зайнятий
