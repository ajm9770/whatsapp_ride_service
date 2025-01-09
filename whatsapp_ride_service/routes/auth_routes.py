"""Authentication routes for the WhatsApp Ride Service application."""

from flask import Blueprint, current_app, jsonify, request
from ..auth import UserManager
import jwt

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()
    user_manager = UserManager(current_app.db_session)

    try:
        user = user_manager.create_user(
            name=data["name"],
            email=data["email"],
            phone_number=data["phone_number"],
            password=data["password"],
        )

        token = jwt.encode(
            {"user_id": user.id},
            current_app.config["JWT_SECRET_KEY"],
            algorithm="HS256",
        )

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

    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login a user."""
    data = request.get_json()
    user_manager = UserManager(current_app.db_session)

    try:
        user = user_manager.authenticate_user(
            phone_number=data["phone_number"], password=data["password"]
        )

        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        token = jwt.encode(
            {"user_id": user.id},
            current_app.config["JWT_SECRET_KEY"],
            algorithm="HS256",
        )

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

    except KeyError:
        return jsonify({"error": "Missing phone number or password"}), 400
