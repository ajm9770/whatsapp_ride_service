from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from .models import User
from sqlalchemy.orm import Session
import re
import bcrypt

def get_token_from_header():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ')[1]

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = current_app.db_session.get(User, data['user_id'])  # Updated to session.get()
            
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

def validate_password(password):
    """
    Validate password strength:
    - At least 8 characters long
    - Contains at least one uppercase letter
    - Contains at least one lowercase letter
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
        
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
        
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
        
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
        
    return True, None

def validate_phone_number(phone):
    """Validate phone number format (E.164)"""
    if not re.match(r"^\+[1-9]\d{1,14}$", phone):
        return False, "Invalid phone number format. Must be in E.164 format (e.g. +1234567890)"
    return True, None

def validate_email(email):
    """Validate email format"""
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return False, "Invalid email format"
    return True, None

class UserManager:
    def __init__(self, session):
        self.session = session
        
    def create_user(self, name, email, phone_number, password):
        # Validate input
        if not name or not email or not phone_number or not password:
            raise ValueError("All fields are required")
            
        # Validate password strength
        is_valid, msg = validate_password(password)
        if not is_valid:
            raise ValueError(msg)
            
        # Validate phone number
        is_valid, msg = validate_phone_number(phone_number)
        if not is_valid:
            raise ValueError(msg)
            
        # Validate email
        is_valid, msg = validate_email(email)
        if not is_valid:
            raise ValueError(msg)
            
        # Check if user already exists
        existing_user = self.session.query(User).filter(
            (User.email == email) | (User.phone_number == phone_number)
        ).first()
        if existing_user:
            raise ValueError("User with this email or phone number already exists")
            
        # Create user
        user = User(
            name=name,
            email=email,
            phone_number=phone_number
        )
        user.set_password(password)  # Use the model's set_password method
        
        self.session.add(user)
        self.session.commit()
        
        return user
        
    def authenticate_user(self, phone_number, password):
        user = self.session.query(User).filter_by(phone_number=phone_number).first()
        
        if user and user.check_password(password):  # Use the model's check_password method
            return user
            
        return None
        
    def update_user(self, user_id, name=None, email=None, phone_number=None):
        user = self.session.get(User, user_id)  # Updated to session.get()
        if not user:
            raise ValueError("User not found")
            
        if name:
            user.name = name
        if email:
            is_valid, msg = validate_email(email)
            if not is_valid:
                raise ValueError(msg)
            user.email = email
        if phone_number:
            is_valid, msg = validate_phone_number(phone_number)
            if not is_valid:
                raise ValueError(msg)
            user.phone_number = phone_number
            
        self.session.commit()
        return user
        
    def update_password(self, user, new_password):
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            raise ValueError(msg)
            
        user.set_password(new_password)  # Use the model's set_password method
        self.session.commit()
        
    def verify_password(self, user, password):
        return user.check_password(password)  # Use the model's check_password method
