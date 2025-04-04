# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from models import db, User # Імпортуємо db та User з models.py

load_dotenv()

app = Flask(__name__)

# --- Конфігурація ---
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') # Дуже важливо для сесій!

# Налаштування підключення до бази даних db4free (MySQL)
db_user = os.getenv('DATABASE_USER')
db_password = os.getenv('DATABASE_PASSWORD')
db_host = os.getenv('DATABASE_HOST')
db_name = os.getenv('DATABASE_NAME')
# Увага: Використовуємо mysql+mysqlconnector
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Вимикаємо відстеження змін, щоб не було попереджень

# --- Ініціалізація розширень ---
db.init_app(app) # Пов'язуємо SQLAlchemy з нашим додатком Flask

# --- Створення таблиць (якщо їх ще немає) ---
# Це потрібно виконати один раз при першому запуску або після змін моделі
# В продакшені краще використовувати інструменти міграцій (Alembic)
with app.app_context():
    try:
        print("Спроба створити таблиці бази даних...")
        db.create_all()
        print("Таблиці успішно створено (або вже існували).")
    except Exception as e:
        print(f"Помилка при створенні таблиць: {e}")
        # Можливо, база даних ще недоступна при першому запуску на Render
        # Render може перезапустити додаток, і тоді все спрацює.

# --- Маршрути (Routes) ---

@app.route('/')
def index():
    """Головна сторінка: перенаправляє на сторінку привітання, якщо користувач увійшов,
       інакше показує сторінку входу/реєстрації."""
    if 'user_id' in session:
        return redirect(url_for('welcome'))
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    """Обробляє реєстрацію нового користувача."""
    if 'user_id' in session:
        return redirect(url_for('welcome')) # Якщо вже увійшов, не реєструвати

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Будь ласка, введіть ім\'я користувача та пароль.', 'error')
        return redirect(url_for('index'))

    # Перевірка, чи існує користувач
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Це ім\'я користувача вже зайняте. Спробуйте інше.', 'error')
        return redirect(url_for('index'))

    # Створення нового користувача
    new_user = User(username=username)
    new_user.set_password(password) # Хешуємо пароль

    try:
        db.session.add(new_user)
        db.session.commit()
        flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
        # Автоматичний вхід після реєстрації (опціонально):
        # session['user_id'] = new_user.id
        # session['username'] = new_user.username
        # return redirect(url_for('welcome'))
        return redirect(url_for('index')) # Перенаправляємо на логін після реєстрації
    except Exception as e:
        db.session.rollback() # Відкат змін у разі помилки
        flash(f'Помилка реєстрації: {e}', 'error')
        print(f"Помилка при додаванні користувача: {e}") # Для дебагу на сервері
        return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    """Обробляє спробу входу користувача."""
    if 'user_id' in session:
        return redirect(url_for('welcome')) # Якщо вже увійшов

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Будь ласка, введіть ім\'я користувача та пароль.', 'error')
        return redirect(url_for('index'))

    user = User.query.filter_by(username=username).first()

    # Перевірка користувача і пароля
    if user and user.check_password(password):
        # Успішний вхід - зберігаємо ID та ім'я користувача в сесії
        session['user_id'] = user.id
        session['username'] = user.username
        flash('Вхід успішний!', 'success')
        return redirect(url_for('welcome'))
    else:
        flash('Неправильне ім\'я користувача або пароль.', 'error')
        return redirect(url_for('index'))

@app.route('/welcome')
def welcome():
    """Сторінка привітання для залогінених користувачів."""
    # Захист сторінки: якщо користувач не в сесії, перенаправити на вхід
    if 'user_id' not in session:
        flash('Будь ласка, увійдіть, щоб побачити цю сторінку.', 'warning')
        return redirect(url_for('index'))

    # Отримуємо ім'я користувача з сесії
    username = session.get('username', 'Гість') # 'Гість' як запасний варіант
    return render_template('welcome.html', username=username)

@app.route('/logout')
def logout():
    """Вихід користувача з системи."""
    # Видаляємо дані користувача з сесії
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Ви успішно вийшли з системи.', 'info')
    return redirect(url_for('index'))

# Запуск додатку (тільки для локальної розробки)
# На Render буде використовуватись Gunicorn
if __name__ == '__main__':
    app.run(debug=True) # debug=True зручно для розробки, але вимкни в продакшені
