from app import app, db, User, Room, Service, Booking, Review
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Очищаем все таблицы
        db.drop_all()
        
        # Создаем все таблицы
        db.create_all()
        
        # Создаем пользователей
        users = [
            User(username='admin', password=generate_password_hash('admin123'), role='admin', email='admin@hotel.com'),
            User(username='manager', password=generate_password_hash('manager123'), role='manager', email='manager@hotel.com'),
            User(username='client1', password=generate_password_hash('client123'), role='client', email='client1@example.com'),
            User(username='client2', password=generate_password_hash('client123'), role='client', email='client2@example.com'),
            User(username='client3', password=generate_password_hash('client123'), role='client', email='client3@example.com')
        ]

        # Создаем номера
        rooms = [
            Room(number='101', type='Стандарт', price=2500, capacity=2, 
                 description='Номер с одной кроватью, телевизор, Wi-Fi', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Душ, Кондиционер'),
            Room(number='102', type='Стандарт', price=2500, capacity=2, 
                 description='Номер с одной кроватью, телевизор, Wi-Fi', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Душ, Кондиционер'),
            Room(number='201', type='Люкс', price=5000, capacity=2, 
                 description='Номер с большой кроватью, гостиная, мини-бар', 
                 images='1_image-1742554462077-529878768.jpg,1_1742389451583-690884437.jpg', 
                 tags='Wi-Fi, Телевизор, Мини-бар, Джакузи, Вид на город'),
            Room(number='202', type='Люкс', price=5000, capacity=2, 
                 description='Номер с большой кроватью, гостиная, мини-бар', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Мини-бар, Джакузи, Вид на город'),
            Room(number='301', type='Семейный', price=4000, capacity=4, 
                 description='Две спальни, гостиная, кухня', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Кухня, Балкон, Семейный, Кондиционер'),
            Room(number='302', type='Семейный', price=4000, capacity=4, 
                 description='Две спальни, гостиная, кухня', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Кухня, Балкон, Семейный, Кондиционер'),
            Room(number='401', type='Президентский', price=10000, capacity=2, 
                 description='Роскошный номер с панорамным видом', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Джакузи, Мини-бар, Сауна, Панорамный вид, VIP'),
            Room(number='402', type='Президентский', price=10000, capacity=2, 
                 description='Роскошный номер с панорамным видом', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Джакузи, Мини-бар, Сауна, Панорамный вид, VIP'),
            Room(number='501', type='Бизнес', price=3500, capacity=2, 
                 description='Номер для деловых поездок', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Рабочая зона, Кофемашина, Бизнес'),
            Room(number='502', type='Бизнес', price=3500, capacity=2, 
                 description='Номер для деловых поездок', 
                 images='[]', 
                 tags='Wi-Fi, Телевизор, Рабочая зона, Кофемашина, Бизнес')
        ]

        # Создаем услуги
        services = [
            Service(name='Завтрак', price=500, description='Шведский стол'),
            Service(name='Ужин', price=1000, description='Трехразовое питание'),
            Service(name='Трансфер', price=1500, description='Трансфер из/в аэропорт'),
            Service(name='СПА', price=2000, description='СПА-процедуры'),
            Service(name='Экскурсия', price=2500, description='Обзорная экскурсия по городу'),
            Service(name='Прачечная', price=500, description='Стирка и глажка одежды'),
            Service(name='Парковка', price=300, description='Охраняемая парковка'),
            Service(name='Конференц-зал', price=5000, description='Аренда конференц-зала'),
            Service(name='Фитнес', price=800, description='Доступ в фитнес-зал'),
            Service(name='Мини-бар', price=0, description='Мини-бар в номере')
        ]

        # Создаем бронирования
        bookings = [
            Booking(user=users[2], room=rooms[0], check_in=datetime.now(), check_out=datetime.now() + timedelta(days=3), status='confirmed', total_price=7500),
            Booking(user=users[3], room=rooms[2], check_in=datetime.now() + timedelta(days=1), check_out=datetime.now() + timedelta(days=4), status='pending', total_price=15000),
        ]

        # Добавляем все объекты в сессию
        for user in users:
            db.session.add(user)
        for room in rooms:
            db.session.add(room)
        for service in services:
            db.session.add(service)
        for booking in bookings:
            db.session.add(booking)

        # Сохраняем изменения
        db.session.commit()

if __name__ == '__main__':
    init_db()
    print('База данных успешно инициализирована!') 