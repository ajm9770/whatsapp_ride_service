"""User routes for the WhatsApp Ride Service application."""

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..auth import UserManager, token_required

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/register", methods=["POST"])
def register_user():
    """Register a new user."""
    data = request.get_json()
    required_fields = ["name", "email", "phone_number", "password"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    user_manager = UserManager(current_app.db_session)

    try:
        user = user_manager.create_user(
            name=data["name"],
            email=data["email"],
            phone_number=data["phone_number"],
            password=data["password"],
        )

        token = user_manager.generate_token(user)

        return (
            jsonify(
                {
                    "token": token,
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "phone_number": user.phone_number,
                    },
                }
            ),
            201,
        )

    except IntegrityError as e:
        return jsonify({"error": "User already exists"}), 409

    except Exception as e:
        return jsonify({"error": "Failed to create user"}), 500


@user_bp.route("/login", methods=["POST"])
def login():
    """Login a user."""
    data = request.get_json()

    if not data or not data.get("phone_number") or not data.get("password"):
        return jsonify({"error": "Missing phone number or password"}), 400

    try:
        user_manager = UserManager(current_app.db_session)
        user = user_manager.authenticate_user(
            phone_number=data["phone_number"], password=data["password"]
        )

        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        token = user_manager.generate_token(user)

        return jsonify(
            {
                "token": token,
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": "An error occurred"}), 500


@user_bp.route("/profile", methods=["GET"])
@token_required
def get_profile(current_user):
    """Get the current user's profile."""
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    try:
        return (
            jsonify(
                {
                    "id": current_user.id,
                    "name": current_user.name,
                    "email": current_user.email,
                    "phone_number": current_user.phone_number,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to get user profile"}), 500


@user_bp.route("/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    """Update the current user's profile."""
    data = request.get_json()

    try:
        user_manager = UserManager(current_app.db_session)
        user = user_manager.update_user(
            current_user.id,
            name=data.get("name"),
            email=data.get("email"),
            phone_number=data.get("phone_number"),
        )

        return (
            jsonify(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "phone_number": user.phone_number,
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to update user profile"}), 500


@user_bp.route("/profile", methods=["DELETE"])
@token_required
def delete_profile(current_user):
    """Delete the current user's profile."""
    try:
        user_manager = UserManager(current_app.db_session)
        user_manager.delete_user(current_user.id)
        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": "Failed to delete user"}), 500


@user_bp.route("/password", methods=["PUT"])
@token_required
def change_password(current_user):
    """Change the current user's password."""
    data = request.get_json()
    user_manager = UserManager(current_app.db_session)

    try:
        if not user_manager.verify_password(current_user, data["current_password"]):
            return jsonify({"error": "Current password is incorrect"}), 401

        user_manager.update_password(current_user, data["new_password"])
        return jsonify({"message": "Password updated successfully"})

    except KeyError:
        return jsonify({"error": "Missing required fields"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/rides", methods=["GET"])
@token_required
def get_user_rides(current_user):
    """Get all rides for the current user."""
    from ..database_ops import DatabaseOps

    try:
        db_ops = DatabaseOps(current_app.db_session)
        rides = db_ops.get_user_rides(current_user.id)

        return (
            jsonify(
                {
                    "rides": [
                        {
                            "id": ride.id,
                            "pickup_location": ride.pickup_location,
                            "dropoff_location": ride.dropoff_location,
                            "status": ride.status,
                            "driver_id": ride.driver_id,
                            "created_at": str(ride.created_at),
                        }
                        for ride in rides
                    ]
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to get user rides"}), 500


@user_bp.route("/payments", methods=["GET"])
@token_required
def get_user_payments(current_user):
    """Get all payments for the current user."""
    from ..database_ops import DatabaseOps

    try:
        db_ops = DatabaseOps(current_app.db_session)
        payments = db_ops.get_user_payments(current_user.id)

        return (
            jsonify(
                {
                    "payments": [
                        {
                            "id": payment.id,
                            "ride_id": payment.ride_id,
                            "amount": payment.amount,
                            "status": payment.status,
                            "created_at": str(payment.created_at),
                        }
                        for payment in payments
                    ]
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": "Failed to get user payments"}), 500
