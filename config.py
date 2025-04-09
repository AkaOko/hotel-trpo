import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-1234567890-abcdefghijklmnopqrstuvwxyz')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///hotel.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/room_images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max-limit
    INSTANCE_PATH = None  # Отключаем создание директории instance 