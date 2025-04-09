import unittest
from datetime import datetime, timedelta
from models import Room, Booking, User
from extensions import db
from app import app
import os

class TestRoom(unittest.TestCase):
    def setUp(self):
        # Настраиваем тестовое приложение
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        # Создаем контекст приложения
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Создаем тестовую базу данных
        db.create_all()
        
        # Создаем тестового пользователя
        self.user = User(
            username='test_user',
            password='test_password',
            role='client',
            email='test@example.com'
        )
        db.session.add(self.user)
        db.session.commit()
        
        # Создаем тестовый номер
        self.room = Room(
            number='101',
            type='Standard',
            price=100.0,
            capacity=2,
            description='Test room',
            images='[]',
            tags='test,tag'
        )
        db.session.add(self.room)
        db.session.commit()

    def tearDown(self):
        # Очищаем базу данных после тестов
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_is_available_no_bookings(self):
        """Тест проверки доступности номера без бронирований"""
        check_in = datetime.now() + timedelta(days=1)
        check_out = check_in + timedelta(days=3)
        
        self.assertTrue(self.room.is_available(check_in, check_out))

    def test_is_available_with_overlapping_booking(self):
        """Тест проверки доступности номера с пересекающимся бронированием"""
        # Создаем бронирование
        booking = Booking(
            user_id=self.user.id,
            room_id=self.room.id,
            check_in=datetime.now() + timedelta(days=2),
            check_out=datetime.now() + timedelta(days=4),
            status='confirmed',
            total_price=200.0
        )
        db.session.add(booking)
        db.session.commit()
        
        # Проверяем даты, которые пересекаются с существующим бронированием
        check_in = datetime.now() + timedelta(days=1)
        check_out = check_in + timedelta(days=3)
        
        self.assertFalse(self.room.is_available(check_in, check_out))

    def test_is_available_past_date(self):
        """Тест проверки доступности номера с датой в прошлом"""
        check_in = datetime.now() - timedelta(days=1)
        check_out = datetime.now() + timedelta(days=1)
        
        self.assertFalse(self.room.is_available(check_in, check_out))

    def test_is_available_invalid_dates(self):
        """Тест проверки доступности номера с некорректными датами"""
        check_in = datetime.now() + timedelta(days=3)
        check_out = datetime.now() + timedelta(days=1)  # Дата выезда раньше даты заезда
        
        self.assertFalse(self.room.is_available(check_in, check_out))

    def test_get_booked_dates(self):
        """Тест получения списка занятых дат для номера"""
        # Создаем бронирование на 3 дня
        check_in = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        check_out = check_in + timedelta(days=3)
        
        booking = Booking(
            user_id=self.user.id,
            room_id=self.room.id,
            check_in=check_in,
            check_out=check_out,
            status='confirmed',
            total_price=300.0
        )
        db.session.add(booking)
        db.session.commit()
        
        # Получаем список занятых дат
        booked_dates = self.room.get_booked_dates()
        
        # Проверяем, что список содержит правильные даты
        expected_dates = [
            check_in.strftime('%Y-%m-%d'),
            (check_in + timedelta(days=1)).strftime('%Y-%m-%d'),
            (check_in + timedelta(days=2)).strftime('%Y-%m-%d')
        ]
        
        self.assertEqual(len(booked_dates), 3)
        self.assertEqual(set(booked_dates), set(expected_dates))
        
        # Проверяем, что дата выезда не включена в список
        self.assertNotIn(check_out.strftime('%Y-%m-%d'), booked_dates)

if __name__ == '__main__':
    unittest.main() 