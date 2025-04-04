# models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime # Імпортуємо datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Зв'язок із завданнями: 'tasks' - це список завдань користувача
    # backref='owner' дозволяє отримати користувача з об'єкта Task (task.owner)
    # lazy=True означає, що завдання завантажуватимуться лише тоді, коли до них звернуться
    tasks = db.relationship('Task', backref='owner', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Нова модель для завдань
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(20), nullable=False, default='general') # spring, summer, autumn, winter, general
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) # Додаємо час створення
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Зв'язок з User.id

    def __repr__(self):
        return f'<Task {self.content[:30]}>'
