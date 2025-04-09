from app import app, db
from models import Booking
from datetime import datetime

def update_booking_dates():
    with app.app_context():
        # Получаем все бронирования
        bookings = Booking.query.all()
        
        for booking in bookings:
            # Преобразуем DateTime в Date
            if isinstance(booking.check_in, datetime):
                booking.check_in = booking.check_in.date()
            if isinstance(booking.check_out, datetime):
                booking.check_out = booking.check_out.date()
        
        # Сохраняем изменения
        db.session.commit()
        print("База данных успешно обновлена")

if __name__ == '__main__':
    update_booking_dates() 