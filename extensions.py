from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

class CustomSQLAlchemy(SQLAlchemy):
    def init_app(self, app):
        # Устанавливаем временную директорию для instance
        app.instance_path = os.environ.get('FLASK_INSTANCE_PATH', '/tmp')
        super().init_app(app)

db = CustomSQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login' 