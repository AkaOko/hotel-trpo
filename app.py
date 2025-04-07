from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модели базы данных
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
    is_available = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Добавляем отношения
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    room = db.relationship('Room', backref=db.backref('bookings', lazy=True))

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Добавляем отношения
    user = db.relationship('User', backref=db.backref('reviews', lazy=True))
    room = db.relationship('Room', backref=db.backref('reviews', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршруты
@app.route('/')
def index():
    rooms = Room.query.filter_by(is_available=True).all()
    return render_template('index.html', rooms=rooms)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверные учетные данные')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    if request.method == 'POST':
        check_in = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d')
        check_out = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d')
        booking = Booking(
            user_id=current_user.id,
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            total_price=room.price
        )
        db.session.add(booking)
        room.is_available = False
        db.session.commit()
        flash('Бронирование успешно создано')
        return redirect(url_for('index'))
    return render_template('book.html', room=room)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Пароли не совпадают')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='client'
        )
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.')
        return redirect(url_for('login'))

    return render_template('register.html')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Доступ запрещен')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    rooms_count = Room.query.count()
    active_bookings = Booking.query.filter(Booking.check_out > datetime.now()).count()
    users_count = User.query.count()
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         rooms_count=rooms_count,
                         active_bookings=active_bookings,
                         users_count=users_count,
                         recent_bookings=recent_bookings)

@app.route('/admin/rooms')
@login_required
@admin_required
def admin_rooms():
    rooms = Room.query.all()
    return render_template('admin/rooms.html', rooms=rooms)

@app.route('/admin/services')
@login_required
@admin_required
def admin_services():
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/add', methods=['POST'])
@login_required
@admin_required
def admin_add_service():
    name = request.form.get('name')
    price = float(request.form.get('price'))
    description = request.form.get('description')

    service = Service(name=name, price=price, description=description)
    db.session.add(service)
    db.session.commit()

    flash('Услуга успешно добавлена')
    return redirect(url_for('admin_services'))

@app.route('/admin/services/<int:service_id>/edit', methods=['POST'])
@login_required
@admin_required
def admin_edit_service(service_id):
    service = Service.query.get_or_404(service_id)
    
    service.name = request.form.get('name')
    service.price = float(request.form.get('price'))
    service.description = request.form.get('description')
    
    db.session.commit()
    flash('Услуга успешно обновлена')
    return redirect(url_for('admin_services'))

@app.route('/admin/services/<int:service_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_service(service_id):
    service = Service.query.get_or_404(service_id)
    db.session.delete(service)
    db.session.commit()
    flash('Услуга успешно удалена')
    return redirect(url_for('admin_services'))

@app.route('/admin/bookings')
@login_required
@admin_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/bookings/<int:booking_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if request.method == 'POST':
        booking.check_in = datetime.strptime(request.form.get('check_in'), '%Y-%m-%d')
        booking.check_out = datetime.strptime(request.form.get('check_out'), '%Y-%m-%d')
        booking.status = request.form.get('status')
        booking.total_price = float(request.form.get('total_price'))
        db.session.commit()
        flash('Бронирование успешно обновлено')
        return redirect(url_for('admin_bookings'))
    return render_template('admin/edit_booking.html', booking=booking)

@app.route('/admin/bookings/<int:booking_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    db.session.commit()
    flash('Бронирование успешно удалено')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/add', methods=['POST'])
@login_required
@admin_required
def admin_add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if User.query.filter_by(username=username).first():
        flash('Пользователь с таким именем уже существует')
        return redirect(url_for('admin_users'))

    if User.query.filter_by(email=email).first():
        flash('Пользователь с таким email уже существует')
        return redirect(url_for('admin_users'))

    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()
    flash('Пользователь успешно добавлен')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    user = User.query.get_or_404(user_id)
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if username != user.username and User.query.filter_by(username=username).first():
        flash('Пользователь с таким именем уже существует')
        return redirect(url_for('admin_users'))

    if email != user.email and User.query.filter_by(email=email).first():
        flash('Пользователь с таким email уже существует')
        return redirect(url_for('admin_users'))

    user.username = username
    user.email = email
    if password:
        user.password = generate_password_hash(password)
    user.role = role

    db.session.commit()
    flash('Пользователь успешно обновлен')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Нельзя удалить текущего пользователя')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь успешно удален')
    return redirect(url_for('admin_users'))

@app.route('/admin/rooms/add', methods=['POST'])
@login_required
@admin_required
def admin_add_room():
    number = request.form.get('number')
    type = request.form.get('type')
    price = float(request.form.get('price'))
    capacity = int(request.form.get('capacity'))
    description = request.form.get('description')

    if Room.query.filter_by(number=number).first():
        flash('Номер с таким номером уже существует')
        return redirect(url_for('admin_rooms'))

    room = Room(
        number=number,
        type=type,
        price=price,
        capacity=capacity,
        description=description
    )
    db.session.add(room)
    db.session.commit()

    flash('Номер успешно добавлен')
    return redirect(url_for('admin_rooms'))

@app.route('/admin/rooms/<int:room_id>/edit', methods=['POST'])
@login_required
@admin_required
def admin_edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    
    room.type = request.form.get('type')
    room.price = float(request.form.get('price'))
    room.capacity = int(request.form.get('capacity'))
    room.description = request.form.get('description')
    
    db.session.commit()
    flash('Номер успешно обновлен')
    return redirect(url_for('admin_rooms'))

@app.route('/admin/rooms/<int:room_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    
    # Проверяем, нет ли активных бронирований
    active_bookings = Booking.query.filter(
        Booking.room_id == room_id,
        Booking.check_out > datetime.now()
    ).first()
    
    if active_bookings:
        flash('Нельзя удалить номер с активными бронированиями')
        return redirect(url_for('admin_rooms'))
    
    db.session.delete(room)
    db.session.commit()
    
    flash('Номер успешно удален')
    return redirect(url_for('admin_rooms'))

@app.route('/profile')
@login_required
def profile():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('profile.html', bookings=bookings)

@app.route('/profile/edit', methods=['POST'])
@login_required
def edit_profile():
    email = request.form.get('email')
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if email != current_user.email:
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует')
            return redirect(url_for('profile'))
        current_user.email = email

    if current_password:
        if not check_password_hash(current_user.password, current_password):
            flash('Неверный текущий пароль')
            return redirect(url_for('profile'))
        
        if new_password != confirm_password:
            flash('Новые пароли не совпадают')
            return redirect(url_for('profile'))
        
        current_user.password = generate_password_hash(new_password)

    db.session.commit()
    flash('Профиль успешно обновлен')
    return redirect(url_for('profile'))

@app.route('/review', methods=['POST'])
@login_required
def leave_review():
    booking_id = request.form.get('booking_id')
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')

    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Ошибка доступа')
        return redirect(url_for('profile'))

    review = Review(
        user_id=current_user.id,
        room_id=booking.room_id,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()

    flash('Отзыв успешно добавлен')
    return redirect(url_for('profile'))

@app.route('/admin/users/<int:user_id>')
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 