from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import bcrypt
import jwt

Base = declarative_base()

class Driver(Base):
    __tablename__ = 'drivers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    current_latitude = Column(Float)
    current_longitude = Column(Float)
    is_available = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    stripe_customer_id = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def generate_token(self):
        payload = {
            'user_id': self.id,
            'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')

class Ride(Base):
    __tablename__ = 'rides'
    
    id = Column(Integer, primary_key=True)
    passenger_id = Column(Integer, ForeignKey('users.id'))
    passenger_phone = Column(String(20), nullable=False)
    driver_id = Column(Integer, ForeignKey('drivers.id'))
    pickup_latitude = Column(Float, nullable=False)
    pickup_longitude = Column(Float, nullable=False)
    destination_latitude = Column(Float, nullable=False)
    destination_longitude = Column(Float, nullable=False)
    status = Column(String(20), default='requested')  # requested, accepted, in_progress, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    driver = relationship("Driver")
    passenger = relationship("User")
    payment = relationship("Payment", uselist=False, back_populates="ride")

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    ride_id = Column(Integer, ForeignKey('rides.id'), nullable=False)
    amount = Column(Float, nullable=False)
    stripe_payment_intent_id = Column(String(100), unique=True)
    status = Column(String(20), default='pending')  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    ride = relationship("Ride", back_populates="payment")
