"""Authentication routes"""
from flask import Blueprint, request, jsonify, current_app
from ..auth import UserManager
import jwt

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_manager = UserManager(current_app.db_session)
    
    try:
        user = user_manager.create_user(
            name=data['name'],
            email=data['email'],
            phone_number=data['phone_number'],
            password=data['password']
        )
        
        token = jwt.encode(
            {'user_id': user.id},
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone_number': user.phone_number
            }
        }), 201
        
    except (KeyError, ValueError) as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user_manager = UserManager(current_app.db_session)
    
    try:
        user = user_manager.authenticate_user(
            phone_number=data['phone_number'],
            password=data['password']
        )
        
        if user:
            token = jwt.encode(
                {'user_id': user.id},
                current_app.config['JWT_SECRET_KEY'],
                algorithm='HS256'
            )
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'phone_number': user.phone_number
                }
            })
            
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except KeyError:
        return jsonify({'error': 'Missing required fields'}), 400
