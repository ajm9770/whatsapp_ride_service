from flask import Blueprint, request, jsonify
from ..auth import UserManager, token_required
from .. import db
from sqlalchemy.exc import IntegrityError

user_bp = Blueprint('user', __name__)

@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required_fields = ['name', 'email', 'phone_number', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        user_manager = UserManager(db.session)
        user = user_manager.create_user(
            name=data['name'],
            email=data['email'],
            phone_number=data['phone_number'],
            password=data['password']
        )
        
        token = user.generate_token()
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number
            }
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'User already exists'}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'An error occurred'}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('phone_number') or not data.get('password'):
        return jsonify({'error': 'Missing phone number or password'}), 400
    
    try:
        user_manager = UserManager(db.session)
        user = user_manager.authenticate_user(
            phone_number=data['phone_number'],
            password=data['password']
        )
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        token = user.generate_token()
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'An error occurred'}), 500

@user_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'phone_number': current_user.phone_number
        }
    })

@user_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    
    try:
        user_manager = UserManager(db.session)
        user = user_manager.update_user_profile(
            user_id=current_user.id,
            name=data.get('name'),
            email=data.get('email')
        )
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number
            }
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'An error occurred'}), 500

@user_bp.route('/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    data = request.get_json()
    
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': 'Missing old or new password'}), 400
    
    try:
        user_manager = UserManager(db.session)
        user_manager.change_password(
            user_id=current_user.id,
            old_password=data['old_password'],
            new_password=data['new_password']
        )
        
        return jsonify({'message': 'Password changed successfully'})
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'An error occurred'}), 500
