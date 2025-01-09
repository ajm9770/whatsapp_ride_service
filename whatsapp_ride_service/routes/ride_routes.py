"""Ride routes"""
from flask import Blueprint, request, jsonify, current_app
from ..auth import token_required
from ..models import Ride, Driver
from ..database_ops import DatabaseOps
from datetime import datetime

bp = Blueprint('ride', __name__, url_prefix='/ride')

@bp.route('/request', methods=['POST'])
@token_required
def request_ride(current_user):
    data = request.get_json()
    db_ops = DatabaseOps(current_app.db_session)
    
    try:
        # Find available drivers
        available_drivers = db_ops.get_available_drivers(
            latitude=data['pickup_latitude'],
            longitude=data['pickup_longitude'],
            radius_km=5
        )
        
        if not available_drivers:
            return jsonify({'error': 'No drivers available'}), 404
            
        # Create ride request
        ride = Ride(
            user_id=current_user.id,
            driver_id=available_drivers[0].id,
            pickup_latitude=data['pickup_latitude'],
            pickup_longitude=data['pickup_longitude'],
            dropoff_latitude=data['dropoff_latitude'],
            dropoff_longitude=data['dropoff_longitude'],
            status='requested',
            created_at=datetime.utcnow()
        )
        
        current_app.db_session.add(ride)
        current_app.db_session.commit()
        
        return jsonify({
            'id': ride.id,
            'driver': {
                'id': available_drivers[0].id,
                'name': available_drivers[0].name,
                'phone_number': available_drivers[0].phone_number
            },
            'status': ride.status
        }), 201
        
    except KeyError:
        return jsonify({'error': 'Missing required fields'}), 400
    except Exception as e:
        current_app.db_session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:ride_id>/status', methods=['PUT'])
@token_required
def update_ride_status(current_user, ride_id):
    data = request.get_json()
    
    try:
        ride = current_app.db_session.get(Ride, ride_id)  
        if not ride:
            return jsonify({'error': 'Ride not found'}), 404
            
        # Only allow driver to update status
        if ride.driver_id != current_user.id:
            return jsonify({'error': 'Not authorized'}), 403
            
        ride.status = data['status']
        if ride.status == 'completed':
            ride.completed_at = datetime.utcnow()
            
        current_app.db_session.commit()
        
        return jsonify({
            'id': ride.id,
            'status': ride.status
        })
        
    except KeyError:
        return jsonify({'error': 'Missing status field'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.db_session.rollback()
        return jsonify({'error': str(e)}), 500
