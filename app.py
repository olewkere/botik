# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from functools import wraps
from models import db, User, Task # Імпортуємо Task
from werkzeug.exceptions import NotFound # Для обробки 404
from datetime import datetime

load_dotenv()
app = Flask(__name__)

# --- Конфігурація ---
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
db_user = os.getenv('DATABASE_USER')
db_password = os.getenv('DATABASE_PASSWORD')
db_host = os.getenv('DATABASE_HOST')
db_name = os.getenv('DATABASE_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Ініціалізація розширень ---
db.init_app(app)

# --- Створення таблиць ---
with app.app_context():
    try:
        print("Спроба створити/оновити таблиці бази даних...")
        db.create_all()
        print("Таблиці успішно створено/оновлено (або вже існували).")
    except Exception as e:
        print(f"Помилка при створенні/оновленні таблиць: {e}")

# --- Контекстний процесор для додавання поточного року ---
@app.context_processor
def inject_current_year():
    """Робить поточний рік доступним для всіх шаблонів."""
    return {'current_year': datetime.utcnow().year}

# --- Декоратор для перевірки входу ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Будь ласка, увійдіть, щоб отримати доступ до цієї сторінки.', 'warning')
            return redirect(url_for('login')) # Перенаправлення на сторінку входу
        return f(*args, **kwargs)
    return decorated_function

# --- Категорії та Емодзі ---
CATEGORIES = {
    'spring': 'Весна 🌱',
    'summer': 'Літо ☀️',
    'autumn': 'Осінь 🍂',
    'winter': 'Зима ❄️',
    'general': 'Загальні 📌'
}

# --- Маршрути ---

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('planner'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # ... (Код реєстрації залишається той самий, що й був) ...
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
     # ... (Код логіну залишається той самий, що й був) ...
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
    # ... (Код виходу залишається той самий, що й був) ...
    username = session.get('username', 'Користувач')
    session.pop('user_id', None)
    session.pop('username', None)
    flash(f'До побачення, {username}! Ви успішно вийшли.', 'info')
    return redirect(url_for('login'))

# --- Маршрути Планувальника ---

@app.route('/planner')
@login_required
def planner():
    # ... (Код планувальника залишається той самий, що й був) ...
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
    # ... (Код додавання завдання залишається той самий, що й був) ...
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
    # ... (Код зміни статусу залишається той самий, що й був) ...
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
    # ... (Код видалення залишається той самий, що й був) ...
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
    # ... (Код редагування залишається той самий, що й був) ...
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

# ! ПОВЕРТАЄМО МАРШРУТ ДЛЯ ЕКСПОРТУ !
@app.route('/export')
@login_required
def export_tasks():
    """Генерує текстове представлення завдань для експорту."""
    user_id = session['user_id']
    user = User.query.get(user_id)
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.category, Task.timestamp.desc()).all()

    if not tasks:
        flash('У вас ще немає завдань для експорту.', 'info')
        return redirect(url_for('planner'))

    export_text_lines = [f"📋 Список завдань для користувача: {user.username}\n"]
    current_category = None
    for task in tasks:
        if task.category != current_category:
            category_name = CATEGORIES.get(task.category, task.category.capitalize())
            export_text_lines.append(f"\n--- {category_name} ---")
            current_category = task.category
        status_emoji = "✔️" if task.is_completed else "⭕"
        export_text_lines.append(f"{status_emoji} {task.content}")

    export_text = "\n".join(export_text_lines)
    return render_template('export.html', export_text=export_text)


# --- Обробник помилок Flask ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# --- Запуск Flask (тільки для локальної розробки) ---
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
