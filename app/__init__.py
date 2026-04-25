from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()  # Спочатку створюємо db без app

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')
    db.init_app(app)

    with app.app_context():
        from app import routes  # обов’язково!
        return app