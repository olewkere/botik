# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from functools import wraps # Для декоратора login_required
from models import db, User, Task # Імпортуємо Task
from werkzeug.exceptions import NotFound # Для обробки 404

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
# Цей блок створить таблицю Task, якщо її ще немає, при наступному запуску
with app.app_context():
    try:
        print("Спроба створити/оновити таблиці бази даних...")
        db.create_all()
        print("Таблиці успішно створено/оновлено (або вже існували).")
    except Exception as e:
        print(f"Помилка при створенні/оновленні таблиць: {e}")

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
# Можна визначити тут, щоб легко змінювати
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
    """Головна сторінка: перенаправляє на планувальник, якщо увійшов, інакше на логін."""
    if 'user_id' in session:
        return redirect(url_for('planner'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Сторінка та обробка реєстрації."""
    if 'user_id' in session:
        return redirect(url_for('planner')) # Якщо вже увійшов, перенаправити

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
            return redirect(url_for('login')) # Перенаправлення на сторінку входу
        except Exception as e:
            db.session.rollback()
            flash(f'Помилка реєстрації: {e}', 'error')
            print(f"Помилка при реєстрації: {e}")
            return render_template('register.html')

    # Метод GET - просто показуємо форму
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Сторінка та обробка входу."""
    if 'user_id' in session:
        return redirect(url_for('planner')) # Якщо вже увійшов

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
            return redirect(url_for('planner')) # Перенаправлення на планувальник
        else:
            flash('Неправильне ім\'я користувача або пароль.', 'error')
            return render_template('login.html')

    # Метод GET - просто показуємо форму
    return render_template('login.html')

@app.route('/logout')
@login_required # Тільки залогінений користувач може вийти
def logout():
    """Вихід користувача."""
    username = session.get('username', 'Користувач')
    session.pop('user_id', None)
    session.pop('username', None)
    flash(f'До побачення, {username}! Ви успішно вийшли.', 'info')
    return redirect(url_for('login')) # Перенаправлення на сторінку входу

# --- Маршрути Планувальника ---

@app.route('/planner')
@login_required # Захищаємо сторінку планувальника
def planner():
    """Відображає сторінку планувальника з завданнями користувача."""
    user_id = session['user_id']
    # Отримуємо всі завдання поточного користувача, сортуємо за категорією та часом
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.category, Task.timestamp.desc()).all()

    # Групуємо завдання за категоріями для зручного відображення в шаблоні
    tasks_by_category = {category_key: [] for category_key in CATEGORIES.keys()}
    for task in tasks:
        if task.category in tasks_by_category:
            tasks_by_category[task.category].append(task)
        else:
            # Якщо раптом є завдання з невідомою категорією, додамо до 'general'
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
        category = 'general' # За замовчуванням, якщо щось пішло не так

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


@app.route('/toggle_task/<int:task_id>', methods=['POST']) # Використовуємо POST для зміни стану
@login_required
def toggle_task(task_id):
    """Відмічає завдання як виконане/невиконане."""
    task = Task.query.get_or_404(task_id) # Отримати завдання або 404

    # Дуже важливо: перевіряємо, чи завдання належить поточному користувачеві
    if task.user_id != session['user_id']:
        flash('У вас немає доступу до цього завдання.', 'danger')
        return redirect(url_for('planner'))

    task.is_completed = not task.is_completed # Змінюємо статус
    try:
        db.session.commit()
        status = "виконано" if task.is_completed else "не виконано"
        flash(f'Статус завдання "{task.content[:20]}..." змінено на "{status}".', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Не вдалося змінити статус завдання: {e}', 'error')
        print(f"Помилка зміни статусу завдання: {e}")

    return redirect(url_for('planner'))

@app.route('/delete_task/<int:task_id>', methods=['POST']) # Використовуємо POST для видалення
@login_required
def delete_task(task_id):
    """Видаляє завдання."""
    task = Task.query.get_or_404(task_id)

    if task.user_id != session['user_id']:
        flash('У вас немає доступу до цього завдання.', 'danger')
        return redirect(url_for('planner'))

    try:
        content_preview = task.content[:20] # Для повідомлення
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

    # Перевірка власника завдання
    if task.user_id != session['user_id']:
        flash('У вас немає доступу до редагування цього завдання.', 'danger')
        return redirect(url_for('planner'))

    if request.method == 'POST':
        new_content = request.form.get('content')
        new_category = request.form.get('category') # Додаємо можливість зміни категорії

        if not new_content:
            flash('Текст завдання не може бути порожнім!', 'error')
            # Повертаємо користувача до форми редагування з поточним завданням
            return render_template('edit_task.html', task=task, categories=CATEGORIES)

        if new_category not in CATEGORIES:
             flash('Невірна категорія!', 'error')
             new_category = task.category # Залишаємо стару категорію у разі помилки

        task.content = new_content
        task.category = new_category # Оновлюємо категорію
        try:
            db.session.commit()
            flash('Завдання успішно оновлено!', 'success')
            return redirect(url_for('planner')) # Повертаємось до списку завдань
        except Exception as e:
            db.session.rollback()
            flash(f'Не вдалося оновити завдання: {e}', 'error')
            print(f"Помилка оновлення завдання: {e}")
            # Повертаємо користувача до форми редагування з поточним завданням
            return render_template('edit_task.html', task=task, categories=CATEGORIES)

    # Метод GET - показуємо форму редагування
    return render_template('edit_task.html', task=task, categories=CATEGORIES)

# --- Обробник помилок ---
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404 # Можна створити простий шаблон 404.html

# --- Запуск (для локальної розробки) ---
if __name__ == '__main__':
    # Вимикаємо debug=True для продакшену/Render
    app.run(debug=False, host='0.0.0.0') # host='0.0.0.0' для доступності в мережі
