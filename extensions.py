from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

class CustomSQLAlchemy(SQLAlchemy):
    def init_app(self, app):
        super().init_app(app)
        # Отключаем создание директории instance
        app.instance_path = None

db = CustomSQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login' 