from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectMultipleField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo

class BookingForm(FlaskForm):
    check_in = DateField('Дата заезда', validators=[DataRequired()], format='%Y-%m-%d')
    check_out = DateField('Дата выезда', validators=[DataRequired()], format='%Y-%m-%d')
    services = StringField('Услуги')
    submit = SubmitField('Забронировать')

class ProfileForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    current_password = PasswordField('Текущий пароль', validators=[Optional()])
    new_password = PasswordField('Новый пароль', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите новый пароль', validators=[EqualTo('new_password', message='Пароли должны совпадать')])
    submit = SubmitField('Сохранить изменения') 