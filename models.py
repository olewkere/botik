# models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Ініціалізація SQLAlchemy (буде пов'язана з додатком в app.py)
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Збільшено довжину для хешу

    def set_password(self, password):
        """Створює хеш пароля."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Перевіряє хеш пароля."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'