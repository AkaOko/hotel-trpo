from datetime import datetime, timedelta, date
from flask_login import UserMixin
from extensions import db
import os

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'manager', 'client'
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    images = db.Column(db.String(1000))  # Храним список изображений как строку
    tags = db.Column(db.String(500))  # Храним теги как строку, разделенную запятыми
    bookings = db.relationship('Booking', back_populates='room', lazy=True)

    @property
    def image_list(self):
        if not self.images or self.images == '[]':
            return []
        try:
            # Удаляем квадратные скобки и пробелы, разбиваем по запятым
            images = self.images.strip('[]').replace(' ', '').split(',')
            # Фильтруем пустые строки и проверяем существование файлов
            return [img for img in images if img and os.path.exists(os.path.join('static/room_images', img))]
        except Exception:
            return []

    @property
    def tag_list(self):
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    def is_available(self, check_in, check_out):
        """Проверяет доступность номера на указанный период"""
        print(f"\nПроверка доступности номера {self.id}")
        print(f"Запрошенные даты: {check_in} - {check_out}")
        
        if check_in >= check_out:
            print("Ошибка: Дата заезда позже или равна дате выезда")
            return False
            
        if check_in < datetime.now().date():
            print("Ошибка: Дата заезда в прошлом")
            return False
            
        # Получаем все активные бронирования для номера
        active_bookings = Booking.query.filter(
            Booking.room_id == self.id,
            Booking.status != 'cancelled'
        ).all()
        
        print(f"Найдено {len(active_bookings)} активных бронирований")
        
        for booking in active_bookings:
            print(f"Проверка пересечения с бронированием {booking.id}:")
            print(f"Бронирование: {booking.check_in} - {booking.check_out}")
            
            # Проверяем пересечение дат
            if (check_in < booking.check_out and check_out > booking.check_in):
                print("Найдено пересечение с существующим бронированием")
                return False
        
        print("Номер доступен на указанные даты")
        return True

    def get_booked_dates(self):
        """Возвращает список занятых дат для номера"""
        try:
            print(f"\nПолучение занятых дат для номера {self.id}")
            
            # Получаем все активные бронирования
            bookings = Booking.query.filter(
                Booking.room_id == self.id,
                Booking.status != 'cancelled'
            ).all()
            
            print(f"Найдено {len(bookings)} активных бронирований")
            
            booked_dates = []
            for booking in bookings:
                print(f"Обработка бронирования {booking.id}: {booking.check_in} - {booking.check_out}")
                
                # Проверяем, что даты корректны
                if not isinstance(booking.check_in, date) or not isinstance(booking.check_out, date):
                    print(f"Предупреждение: Некорректный формат дат в бронировании {booking.id}")
                    continue
                
                current_date = booking.check_in
                while current_date < booking.check_out:
                    booked_dates.append(current_date.strftime('%Y-%m-%d'))
                    current_date += timedelta(days=1)
            
            print(f"Сгенерировано {len(booked_dates)} занятых дат")
            return booked_dates
            
        except Exception as e:
            print(f"Ошибка в get_booked_dates: {str(e)}")
            return []

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='bookings')
    room = db.relationship('Room', back_populates='bookings')

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class BookingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    
    booking = db.relationship('Booking', backref='booking_services')
    service = db.relationship('Service', backref='booking_services')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='reviews')
    room = db.relationship('Room', backref='reviews') 