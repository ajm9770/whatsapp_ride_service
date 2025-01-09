from flask import Blueprint, request, jsonify, current_app
from ..auth import UserManager, token_required
from sqlalchemy.exc import IntegrityError

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    required_fields = ['name', 'email', 'phone_number', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        user_manager = UserManager(current_app.db_session)
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
        current_app.db_session.rollback()
        return jsonify({'error': 'User already exists'}), 409
    except Exception as e:
        current_app.db_session.rollback()
        return jsonify({'error': 'An error occurred'}), 500

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('phone_number') or not data.get('password'):
        return jsonify({'error': 'Missing phone number or password'}), 400
    
    try:
        user_manager = UserManager(current_app.db_session)
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

@bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email,
        'phone_number': current_user.phone_number
    })

@bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    user_manager = UserManager(current_app.db_session)
    
    try:
        user = user_manager.update_user(
            current_user.id,
            name=data.get('name'),
            email=data.get('email'),
            phone_number=data.get('phone_number')
        )
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone_number': user.phone_number
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except IntegrityError:
        current_app.db_session.rollback()
        return jsonify({'error': 'Email or phone number already in use'}), 409

@bp.route('/password', methods=['PUT'])
@token_required
def change_password(current_user):
    data = request.get_json()
    user_manager = UserManager(current_app.db_session)
    
    try:
        if not user_manager.verify_password(current_user, data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
            
        user_manager.update_password(current_user, data['new_password'])
        return jsonify({'message': 'Password updated successfully'})
        
    except KeyError:
        return jsonify({'error': 'Missing required fields'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
