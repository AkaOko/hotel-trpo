from app import app, db, Room

def update_room_tags():
    with app.app_context():
        # Обновляем теги для каждого номера
        rooms = Room.query.all()
        for room in rooms:
            # Базовые теги для всех номеров
            base_tags = ['Wi-Fi', 'Телевизор', 'Кондиционер']
            
            # Дополнительные теги в зависимости от типа номера
            if room.type == 'Стандарт':
                tags = base_tags + ['Душ']
            elif room.type == 'Люкс':
                tags = base_tags + ['Джакузи', 'Мини-бар', 'Гостиная', 'Вид на город']
            elif room.type == 'Полулюкс':
                tags = base_tags + ['Ванная', 'Мини-бар', 'Диван']
            elif room.type == 'Семейный':
                tags = base_tags + ['Кухня', 'Две спальни', 'Ванная']
            elif room.type == 'Президентский':
                tags = base_tags + ['Джакузи', 'Мини-бар', 'Гостиная', 'Панорамный вид', 'Сауна']
            elif room.type == 'Бизнес':
                tags = base_tags + ['Рабочая зона', 'Сейф', 'Кофемашина']
            else:
                tags = base_tags
            
            # Обновляем теги номера
            room.tags = ','.join(tags)
        
        # Сохраняем изменения
        db.session.commit()
        print("Теги номеров успешно обновлены!")

if __name__ == '__main__':
    update_room_tags() 