"""Ride routes for the WhatsApp Ride Service application."""

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..auth import token_required
from ..database_ops import DatabaseOps
from ..models import Ride, Driver
from datetime import datetime

ride_bp = Blueprint("ride", __name__, url_prefix="/rides")


@ride_bp.route("/create", methods=["POST"])
@token_required
def create_ride(current_user):
    """Create a new ride."""
    data = request.get_json()

    required_fields = [
        "pickup_latitude",
        "pickup_longitude",
        "dropoff_latitude",
        "dropoff_longitude",
        "pickup_time",
    ]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    try:
        db_ops = DatabaseOps(current_app.db_session)
        ride = Ride(
            user_id=current_user.id,
            pickup_latitude=data["pickup_latitude"],
            pickup_longitude=data["pickup_longitude"],
            dropoff_latitude=data["dropoff_latitude"],
            dropoff_longitude=data["dropoff_longitude"],
            pickup_time=datetime.fromisoformat(data["pickup_time"]),
            status="requested",
        )
        current_app.db_session.add(ride)
        current_app.db_session.commit()

        return (
            jsonify(
                {
                    "id": ride.id,
                    "user_id": ride.user_id,
                    "pickup_latitude": ride.pickup_latitude,
                    "pickup_longitude": ride.pickup_longitude,
                    "dropoff_latitude": ride.dropoff_latitude,
                    "dropoff_longitude": ride.dropoff_longitude,
                    "pickup_time": str(ride.pickup_time),
                    "status": ride.status,
                }
            ),
            201,
        )

    except IntegrityError:
        current_app.db_session.rollback()
        return jsonify({"error": "Failed to create ride"}), 500


@ride_bp.route("/<int:ride_id>/accept", methods=["POST"])
@token_required
def accept_ride(current_user, ride_id):
    """Accept a ride request."""
    try:
        db_ops = DatabaseOps(current_app.db_session)
        ride = db_ops.get_ride(ride_id)

        if not ride:
            return jsonify({"error": "Ride not found"}), 404

        if ride.status != "pending":
            return jsonify({"error": "Ride is not available"}), 400

        updated_ride = db_ops.update_ride_status(ride_id, "accepted", current_user.id)

        return (
            jsonify(
                {
                    "id": updated_ride.id,
                    "status": updated_ride.status,
                    "driver_id": updated_ride.driver_id,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to accept ride"}), 500


@ride_bp.route("/<int:ride_id>/complete", methods=["POST"])
@token_required
def complete_ride(current_user, ride_id):
    """Complete a ride."""
    try:
        db_ops = DatabaseOps(current_app.db_session)
        ride = db_ops.get_ride(ride_id)

        if not ride:
            return jsonify({"error": "Ride not found"}), 404

        if ride.driver_id != current_user.id:
            return jsonify({"error": "Not authorized"}), 403

        if ride.status != "accepted":
            return jsonify({"error": "Ride cannot be completed"}), 400

        updated_ride = db_ops.update_ride_status(ride_id, "completed")

        return jsonify({"id": updated_ride.id, "status": updated_ride.status}), 200

    except Exception as e:
        return jsonify({"error": "Failed to complete ride"}), 500


@ride_bp.route("/<int:ride_id>/cancel", methods=["POST"])
@token_required
def cancel_ride(current_user, ride_id):
    """Cancel a ride."""
    try:
        db_ops = DatabaseOps(current_app.db_session)
        ride = db_ops.get_ride(ride_id)

        if not ride:
            return jsonify({"error": "Ride not found"}), 404

        if ride.user_id != current_user.id and ride.driver_id != current_user.id:
            return jsonify({"error": "Not authorized"}), 403

        if ride.status not in ["pending", "accepted"]:
            return jsonify({"error": "Ride cannot be cancelled"}), 400

        updated_ride = db_ops.update_ride_status(ride_id, "cancelled")

        return jsonify({"id": updated_ride.id, "status": updated_ride.status}), 200

    except Exception as e:
        return jsonify({"error": "Failed to cancel ride"}), 500
