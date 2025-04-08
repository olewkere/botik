import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from models import db, User

load_dotenv()

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')

db_user = os.getenv('DATABASE_USER')
db_password = os.getenv('DATABASE_PASSWORD')
db_host = os.getenv('DATABASE_HOST')
db_name = os.getenv('DATABASE_NAME')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        print("Спроба створити таблиці бази даних...")
        db.create_all()
        print("Таблиці успішно створено (або вже існували).")
    except Exception as e:
        print(f"Помилка при створенні таблиць: {e}")


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
        return redirect(url_for('welcome'))

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Будь ласка, введіть ім\'я користувача та пароль.', 'error')
        return redirect(url_for('index'))

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Це ім\'я користувача вже зайняте. Спробуйте інше.', 'error')
        return redirect(url_for('index'))

    new_user = User(username=username)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        flash('Реєстрація успішна! Тепер ви можете увійти.', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Помилка реєстрації: {e}', 'error')
        print(f"Помилка при додаванні користувача: {e}")
        return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
    """Обробляє спробу входу користувача."""
    if 'user_id' in session:
        return redirect(url_for('welcome'))

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Будь ласка, введіть ім\'я користувача та пароль.', 'error')
        return redirect(url_for('index'))

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
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
    if 'user_id' not in session:
        flash('Будь ласка, увійдіть, щоб побачити цю сторінку.', 'warning')
        return redirect(url_for('index'))
        
    username = session.get('username', 'Гість')
    return render_template('welcome.html', username=username)


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


@app.route('/logout')
def logout():
    """Вихід користувача з системи."""
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Ви успішно вийшли з системи.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
