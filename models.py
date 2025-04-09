from datetime import datetime, timedelta, date
from flask_login import UserMixin
from extensions import db
import os

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(10), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    images = db.Column(db.String(500))
    tags = db.Column(db.String(200))
    bookings = db.relationship('Booking', backref='room', lazy=True)

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
        overlapping_bookings = Booking.query.filter(
            Booking.room_id == self.id,
            Booking.status != 'cancelled',
            ((Booking.check_in <= check_in) & (Booking.check_out > check_in)) |
            ((Booking.check_in < check_out) & (Booking.check_out >= check_out)) |
            ((Booking.check_in >= check_in) & (Booking.check_out <= check_out))
        ).first()
        return overlapping_bookings is None

    def get_booked_dates(self):
        booked_dates = []
        bookings = Booking.query.filter(
            Booking.room_id == self.id,
            Booking.status != 'cancelled'
        ).all()
        for booking in bookings:
            current_date = booking.check_in
            while current_date < booking.check_out:
                booked_dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
        return booked_dates

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    services = db.relationship('BookingService', backref='booking', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    bookings = db.relationship('BookingService', backref='service', lazy=True)

class BookingService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 