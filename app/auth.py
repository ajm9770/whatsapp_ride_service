from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta
from .models import User
from sqlalchemy.orm import Session
import re

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
            current_user = Session.query(User).get(data['user_id'])
            
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
    
    return True, "Password is valid"

def validate_phone_number(phone):
    """Validate phone number format"""
    phone_pattern = re.compile(r'^\+?1?\d{9,15}$')
    return bool(phone_pattern.match(phone))

def validate_email(email):
    """Validate email format"""
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))

class UserManager:
    def __init__(self, session):
        self.session = session
    
    def create_user(self, name, email, phone_number, password):
        # Validate input
        if not validate_email(email):
            raise ValueError("Invalid email format")
        
        if not validate_phone_number(phone_number):
            raise ValueError("Invalid phone number format")
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            raise ValueError(msg)
        
        # Check if user already exists
        if self.session.query(User).filter(
            (User.email == email) | (User.phone_number == phone_number)
        ).first():
            raise ValueError("User with this email or phone number already exists")
        
        # Create new user
        user = User(
            name=name,
            email=email,
            phone_number=phone_number
        )
        user.set_password(password)
        
        self.session.add(user)
        self.session.commit()
        
        return user
    
    def authenticate_user(self, phone_number, password):
        user = self.session.query(User).filter_by(phone_number=phone_number).first()
        
        if not user or not user.check_password(password):
            return None
            
        return user
    
    def change_password(self, user_id, old_password, new_password):
        user = self.session.query(User).get(user_id)
        
        if not user or not user.check_password(old_password):
            raise ValueError("Invalid current password")
        
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            raise ValueError(msg)
        
        user.set_password(new_password)
        self.session.commit()
        
        return True
    
    def update_user_profile(self, user_id, name=None, email=None):
        user = self.session.query(User).get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        if email and email != user.email:
            if not validate_email(email):
                raise ValueError("Invalid email format")
            if self.session.query(User).filter_by(email=email).first():
                raise ValueError("Email already in use")
            user.email = email
            
        if name:
            user.name = name
            
        self.session.commit()
        return user
