from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, timedelta
import os
import logging
import sys
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import pandas as pd
from io import BytesIO, StringIO
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired
from extensions import db, login_manager
from models import User, Room, Booking, Service, BookingService, Review
from forms import BookingForm, ProfileForm
from config import Config
import csv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Определяем абсолютные пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_DIR = os.path.join(STATIC_DIR, 'room_images')

app = Flask(__name__, 
           static_folder=STATIC_DIR,
           instance_relative_config=True)
app.config.from_object(Config)

# Настройка логирования для Flask
if not app.debug:
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.INFO)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Инициализация расширений
try:
    db.init_app(app)
    login_manager.init_app(app)
    logger.info("Extensions initialized successfully")
except Exception as e:
    logger.error(f"Error initializing extensions: {str(e)}")
    raise

login_manager.login_view = 'login'

from models import User, Room, Booking, Service, BookingService, Review

class BookingForm(FlaskForm):
    check_in = DateField('Дата заезда', validators=[DataRequired()], format='%Y-%m-%d')
    check_out = DateField('Дата выезда', validators=[DataRequired()], format='%Y-%m-%d')
    services = StringField('Услуги')
    submit = SubmitField('Забронировать')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты
@app.route('/')
def index():
    # Получаем все уникальные теги из номеров
    all_tags = []
    rooms = Room.query.all()
    for room in rooms:
        if room.tags:
            tags = [tag.strip() for tag in room.tags.split(',')]
            all_tags.extend(tags)
    
    unique_tags = sorted(list(set(all_tags)))
    
    # Фильтрация по тегам
    selected_tag = request.args.get('tag')
    if selected_tag:
        filtered_rooms = []
        for room in rooms:
            if room.tags and selected_tag in [tag.strip() for tag in room.tags.split(',')]:
                filtered_rooms.append(room)
        rooms = filtered_rooms
    
    return render_template('index.html', rooms=rooms, tags=unique_tags, selected_tag=selected_tag)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверное имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Пользователь с такой почтой уже существует')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email, role='client')
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/room/<int:room_id>')
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    return render_template('room_detail.html', room=room)

@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    form = BookingForm()
    
    # Получаем все доступные услуги
    services = Service.query.filter_by(is_active=True).all()
    
    if form.validate_on_submit():
        check_in = form.check_in.data
        check_out = form.check_out.data
        
        # Проверка доступности номера
        if not room.is_available(check_in, check_out):
            flash('Номер недоступен на выбранные даты')
            return redirect(url_for('book_room', room_id=room_id))
            
        # Расчет общей стоимости номера
        days = (check_out - check_in).days
        total_price = room.price * days
        
        # Создаем бронирование
        booking = Booking(
            user_id=current_user.id,
            room_id=room_id,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price
        )
        db.session.add(booking)
        db.session.commit()
        
        # Обрабатываем выбранные услуги
        selected_services = request.form.getlist('services')
        if selected_services:
            for service_id in selected_services:
                service = Service.query.get(service_id)
                if service:
                    # Добавляем услугу к бронированию
                    booking_service = BookingService(
                        booking_id=booking.id,
                        service_id=service.id
                    )
                    db.session.add(booking_service)
                    
                    # Обновляем общую стоимость бронирования
                    total_price += service.price
            
            # Обновляем общую стоимость с учетом услуг
            booking.total_price = total_price
            db.session.commit()
        
        flash('Бронирование успешно создано')
        return redirect(url_for('my_bookings'))
        
    return render_template('book_room.html', room=room, form=form, services=services)

@app.route('/my_bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm()
    
    if form.validate_on_submit():
        # Проверяем, не занято ли новое имя пользователя
        if form.username.data != current_user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Пользователь с таким именем уже существует')
                return redirect(url_for('edit_profile'))
        
        # Проверяем, не занят ли новый email
        if form.email.data != current_user.email:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash('Пользователь с таким email уже существует')
                return redirect(url_for('edit_profile'))
        
        # Если введен текущий пароль, проверяем его
        if form.current_password.data:
            if not check_password_hash(current_user.password, form.current_password.data):
                flash('Неверный текущий пароль')
                return redirect(url_for('edit_profile'))
            
            # Если введен новый пароль, обновляем его
            if form.new_password.data:
                current_user.password = generate_password_hash(form.new_password.data)
        
        # Обновляем остальные данные
        current_user.username = form.username.data
        current_user.email = form.email.data
        
        db.session.commit()
        flash('Профиль успешно обновлен')
        return redirect(url_for('profile'))
    
    # Заполняем форму текущими данными пользователя
    form.username.data = current_user.username
    form.email.data = current_user.email
    
    return render_template('edit_profile.html', form=form)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    # Получаем статистику
    users_count = User.query.count()
    rooms_count = Room.query.count()
    active_bookings = Booking.query.filter(Booking.status != 'cancelled').count()
    services_count = Service.query.count()
    
    # Получаем последние бронирования
    bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    return render_template('admin/index.html',
                         users_count=users_count,
                         rooms_count=rooms_count,
                         active_bookings=active_bookings,
                         services_count=services_count,
                         bookings=bookings)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['POST'])
@login_required
def admin_add_user():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
        
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    
    if User.query.filter_by(username=username).first():
        flash('Пользователь с таким именем уже существует')
        return redirect(url_for('admin_users'))
        
    if User.query.filter_by(email=email).first():
        flash('Пользователь с такой почтой уже существует')
        return redirect(url_for('admin_users'))
        
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password=hashed_password, email=email, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    flash('Пользователь успешно добавлен')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')
        password = request.form.get('password')
        
        # Проверяем, не занято ли новое имя пользователя
        if username != user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Пользователь с таким именем уже существует')
                return redirect(url_for('admin_edit_user', user_id=user.id))
        
        # Проверяем, не занят ли новый email
        if email != user.email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Пользователь с таким email уже существует')
                return redirect(url_for('admin_edit_user', user_id=user.id))
        
        # Обновляем данные пользователя
        user.username = username
        user.email = email
        user.role = role
        
        # Если введен новый пароль, обновляем его
        if password:
            user.password = generate_password_hash(password)
        
        db.session.commit()
        flash('Пользователь успешно обновлен')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', user=user)

@app.route('/admin/rooms')
@login_required
def admin_rooms():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    rooms = Room.query.all()
    return render_template('admin/rooms.html', rooms=rooms)

@app.route('/admin/rooms/add', methods=['GET', 'POST'])
@login_required
def admin_add_room():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        number = request.form.get('number')
        type = request.form.get('type')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        capacity = int(request.form.get('capacity'))
        tags = request.form.get('tags')
        
        new_room = Room(
            number=number,
            type=type,
            description=description,
            price=price,
            capacity=capacity,
            tags=tags
        )
        
        db.session.add(new_room)
        db.session.commit()
        
        flash('Номер успешно добавлен')
        return redirect(url_for('admin_rooms'))
        
    return render_template('admin/add_room.html')

@app.route('/admin/rooms/edit/<int:room_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_room(room_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
        
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        room.number = request.form.get('number')
        room.type = request.form.get('type')
        room.price = float(request.form.get('price'))
        room.capacity = int(request.form.get('capacity'))
        room.description = request.form.get('description')
        room.tags = request.form.get('tags')
        
        db.session.commit()
        flash('Номер успешно обновлен')
        return redirect(url_for('admin_rooms'))
    
    return render_template('admin/edit_room.html', room=room)

@app.route('/admin/bookings')
@login_required
def admin_bookings():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    bookings = Booking.query.all()
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/bookings/edit/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def edit_booking(booking_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    if request.method == 'POST':
        booking.status = request.form.get('status')
        booking.check_in = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d')
        booking.check_out = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d')
        booking.total_price = float(request.form.get('total_price'))
        
        db.session.commit()
        flash('Бронирование успешно обновлено')
        return redirect(url_for('admin_bookings'))
    
    return render_template('admin/edit_booking.html', booking=booking)

@app.route('/admin/bookings/delete/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Удаляем все связанные услуги
    BookingService.query.filter_by(booking_id=booking.id).delete()
    
    # Удаляем само бронирование
    db.session.delete(booking)
    db.session.commit()
    
    flash('Бронирование успешно удалено')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/services')
@login_required
def admin_services():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/add', methods=['GET', 'POST'])
@login_required
def admin_add_service():
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        
        new_service = Service(name=name, description=description, price=price)
        db.session.add(new_service)
        db.session.commit()
        
        flash('Услуга успешно добавлена')
        return redirect(url_for('admin_services'))
        
    return render_template('admin/add_service.html')

@app.route('/admin/services/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_service(service_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
        
    service = Service.query.get_or_404(service_id)
    
    if request.method == 'POST':
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.price = float(request.form.get('price'))
        
        db.session.commit()
        flash('Услуга успешно обновлена')
        return redirect(url_for('admin_services'))
        
    return render_template('admin/edit_service.html', service=service)

# API endpoints
@app.route('/api/rooms/<int:room_id>/booked-dates')
def get_booked_dates(room_id):
    try:
        print(f"Getting booked dates for room {room_id}")
        room = Room.query.get_or_404(room_id)
        booked_dates = room.get_booked_dates()
        print(f"Found {len(booked_dates)} booked dates: {booked_dates}")
        return jsonify({'booked_dates': booked_dates})
    except Exception as e:
        print(f"Error in get_booked_dates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/rooms/<int:room_id>/availability')
def check_room_availability(room_id):
    try:
        check_in = request.args.get('check_in')
        check_out = request.args.get('check_out')
        
        print(f"\nЗапрос проверки доступности:")
        print(f"ID номера: {room_id}")
        print(f"Дата заезда: {check_in}")
        print(f"Дата выезда: {check_out}")
        
        if not check_in or not check_out:
            print("Ошибка: Не указаны даты заезда и выезда")
            return jsonify({'error': 'Не указаны даты заезда и выезда'}), 400
            
        try:
            check_in_date = datetime.strptime(check_in, '%Y-%m-%d').date()
            check_out_date = datetime.strptime(check_out, '%Y-%m-%d').date()
        except ValueError as e:
            print(f"Ошибка при парсинге дат: {str(e)}")
            return jsonify({'error': f'Неверный формат даты: {str(e)}'}), 400
        
        print(f"Парсинг дат успешен:")
        print(f"Дата заезда (date): {check_in_date}")
        print(f"Дата выезда (date): {check_out_date}")
        
        room = Room.query.get_or_404(room_id)
        print(f"Найден номер: {room.id}")
        
        try:
            available = room.is_available(check_in_date, check_out_date)
            print(f"Результат проверки доступности: {available}")
        except Exception as e:
            print(f"Ошибка в методе is_available: {str(e)}")
            return jsonify({'error': f'Ошибка при проверке доступности: {str(e)}'}), 500
        
        booked_dates = room.get_booked_dates()
        print(f"Занятые даты: {booked_dates}")
        
        return jsonify({
            'available': available,
            'message': 'Доступен' if available else 'Не доступен',
            'booked_dates': booked_dates
        })
    except Exception as e:
        print(f"Неожиданная ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'Пользователь успешно удален'})

@app.route('/api/rooms/<int:room_id>', methods=['DELETE'])
@login_required
def delete_room(room_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    return jsonify({'message': 'Номер успешно удален'})

@app.route('/api/services/<int:service_id>', methods=['DELETE'])
@login_required
def delete_service(service_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Доступ запрещен'}), 403
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    return jsonify({'message': 'Услуга успешно удалена'})

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/rooms/<int:room_id>/upload', methods=['POST'])
@login_required
def upload_room_images(room_id):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
        
    room = Room.query.get_or_404(room_id)
    
    if 'images' not in request.files:
        flash('Файлы не были загружены')
        return redirect(url_for('admin_rooms'))
        
    files = request.files.getlist('images')
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_DIR, filename)
            file.save(file_path)
            
            # Здесь можно добавить логику для сохранения пути к изображению в базе данных
            # Например, если у вас есть модель RoomImage:
            # room_image = RoomImage(room_id=room.id, image_path=filename)
            # db.session.add(room_image)
            
    db.session.commit()
    flash('Изображения успешно загружены')
    return redirect(url_for('admin_rooms'))

@app.route('/admin/rooms/<int:room_id>/images/<filename>', methods=['POST'])
@login_required
def delete_room_image(room_id, filename):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
        
    room = Room.query.get_or_404(room_id)
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('Изображение успешно удалено')
    else:
        flash('Изображение не найдено')
        
    return redirect(url_for('admin_rooms'))

@app.route('/admin/export/<data_type>')
@login_required
def export_data(data_type):
    if current_user.role != 'admin':
        flash('Доступ запрещен')
        return redirect(url_for('index'))
    
    if data_type == 'all':
        # Создаем Excel файл с несколькими листами
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Пользователи
            users = User.query.all()
            users_data = [{
                'ID': user.id,
                'Имя пользователя': user.username,
                'Email': user.email,
                'Роль': user.role,
                'Дата регистрации': user.created_at.strftime('%d.%m.%Y')
            } for user in users]
            pd.DataFrame(users_data).to_excel(writer, sheet_name='Пользователи', index=False)
            
            # Номера
            rooms = Room.query.all()
            rooms_data = [{
                'ID': room.id,
                'Номер': room.number,
                'Тип': room.type,
                'Цена': room.price,
                'Вместимость': room.capacity,
                'Описание': room.description
            } for room in rooms]
            pd.DataFrame(rooms_data).to_excel(writer, sheet_name='Номера', index=False)
            
            # Бронирования
            bookings = Booking.query.all()
            bookings_data = [{
                'ID': booking.id,
                'Пользователь': booking.user.username,
                'Номер': booking.room.number,
                'Дата заезда': booking.check_in.strftime('%d.%m.%Y'),
                'Дата выезда': booking.check_out.strftime('%d.%m.%Y'),
                'Статус': booking.status,
                'Стоимость': booking.total_price
            } for booking in bookings]
            pd.DataFrame(bookings_data).to_excel(writer, sheet_name='Бронирования', index=False)
            
            # Услуги
            services = Service.query.all()
            services_data = [{
                'ID': service.id,
                'Название': service.name,
                'Описание': service.description,
                'Цена': service.price,
                'Активна': 'Да' if service.is_active else 'Нет'
            } for service in services]
            pd.DataFrame(services_data).to_excel(writer, sheet_name='Услуги', index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='hotel_data.xlsx'
        )
    
    else:
        # Используем pandas для создания CSV с правильной кодировкой и разделителями
        if data_type == 'users':
            users = User.query.all()
            data = [{
                'ID': user.id,
                'Имя пользователя': user.username,
                'Email': user.email,
                'Роль': user.role,
                'Дата регистрации': user.created_at.strftime('%d.%m.%Y')
            } for user in users]
            filename = 'users.csv'
            
        elif data_type == 'rooms':
            rooms = Room.query.all()
            data = [{
                'ID': room.id,
                'Номер': room.number,
                'Тип': room.type,
                'Цена': room.price,
                'Вместимость': room.capacity,
                'Описание': room.description
            } for room in rooms]
            filename = 'rooms.csv'
            
        elif data_type == 'bookings':
            bookings = Booking.query.all()
            data = [{
                'ID': booking.id,
                'Пользователь': booking.user.username,
                'Номер': booking.room.number,
                'Дата заезда': booking.check_in.strftime('%d.%m.%Y'),
                'Дата выезда': booking.check_out.strftime('%d.%m.%Y'),
                'Статус': booking.status,
                'Стоимость': booking.total_price
            } for booking in bookings]
            filename = 'bookings.csv'
            
        elif data_type == 'services':
            services = Service.query.all()
            data = [{
                'ID': service.id,
                'Название': service.name,
                'Описание': service.description,
                'Цена': service.price,
                'Активна': 'Да' if service.is_active else 'Нет'
            } for service in services]
            filename = 'services.csv'
        
        # Создаем и настраиваем DataFrame
        df = pd.DataFrame(data)
        
        # Создаем CSV-файл с правильной кодировкой и разделителем
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig', sep=';')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

@app.route('/api/rooms/booked-dates')
def get_all_booked_dates():
    try:
        print("Getting booked dates for all rooms")
        booked_dates = []
        bookings = Booking.query.filter(
            Booking.status != 'cancelled'
        ).all()
        
        print(f"Found {len(bookings)} bookings")
        
        for booking in bookings:
            current_date = booking.check_in
            while current_date < booking.check_out:
                booked_dates.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
                
        print(f"Generated {len(booked_dates)} booked dates")
        return jsonify({'booked_dates': booked_dates})
    except Exception as e:
        print(f"Error in get_all_booked_dates: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {str(error)}")
    return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"Not Found Error: {str(error)}")
    return render_template('404.html'), 404

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    app.run(host='0.0.0.0', port=5000, debug=True) 