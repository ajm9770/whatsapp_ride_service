"""Test suite for the WhatsApp Ride Service application."""

import unittest
from tests import config
from whatsapp_ride_service.models import Base, Driver, Payment, Ride, User
from whatsapp_ride_service import create_app
from whatsapp_ride_service.auth import UserManager
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime


class TestApp(unittest.TestCase):
    """Test cases for the main application functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment before all tests."""
        # Create test app with test config
        cls.app = create_app(config)
        cls.client = cls.app.test_client()
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        # Set up database
        cls.engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        Base.metadata.create_all(cls.engine)
        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()
        cls.app.db_session = cls.session

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment after all tests."""
        cls.session.close()
        Base.metadata.drop_all(cls.engine)
        cls.app_context.pop()

    def setUp(self):
        """Set up test fixtures before each test."""
        # Clear all tables before each test
        with self.app.app_context():
            db = self.app.db_session
            db.query(Payment).delete()
            db.query(Ride).delete()
            db.query(User).delete()
            db.query(Driver).delete()
            db.commit()

    def create_test_user(self):
        """Create a test user for testing."""
        user_manager = UserManager(self.app.db_session)
        return user_manager.create_user(
            name="Test User",
            email="test@example.com",
            phone_number="+1234567890",
            password="TestPass123!",
        )

    def create_test_driver(self):
        """Create a test driver for testing."""
        driver = Driver(
            name="Test Driver",
            phone_number="+1987654321",
            current_latitude=40.7128,
            current_longitude=-74.0060,
            is_available=True,  # Make sure driver is available
        )
        self.app.db_session.add(driver)
        self.app.db_session.commit()
        return driver

    def test_user_registration(self):
        """Test user registration endpoint."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone_number": "+1234567891",
            "password": "SecurePass123!",
        }
        response = self.client.post(
            "/auth/register", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)
        json_data = json.loads(response.data)
        self.assertIn("token", json_data)
        self.assertEqual(json_data["user"]["name"], "John Doe")

    def test_user_login(self):
        """Test user login endpoint."""
        # First create a user
        self.create_test_user()

        # Try logging in
        data = {"phone_number": "+1234567890", "password": "TestPass123!"}
        response = self.client.post(
            "/auth/login", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertIn("token", json_data)

    def test_invalid_login(self):
        """Test login with invalid credentials."""
        # Try logging in with wrong credentials
        data = {"phone_number": "+1234567890", "password": "WrongPass123!"}
        response = self.client.post(
            "/auth/login", data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 401)

    def test_protected_route(self):
        """Test access to protected routes."""
        # Try accessing protected route without token
        response = self.client.get("/user/profile")

        self.assertEqual(response.status_code, 401)

        # Register and login to get token
        user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone_number": "+1234567890",
            "password": "TestPass123!",
        }
        self.client.post(
            "/auth/register",
            data=json.dumps(user_data),
            content_type="application/json",
        )

        login_response = self.client.post(
            "/auth/login",
            data=json.dumps(
                {"phone_number": "+1234567890", "password": "TestPass123!"}
            ),
            content_type="application/json",
        )
        token = json.loads(login_response.data)["token"]

        # Access protected route with token
        response = self.client.get(
            "/user/profile", headers={"Authorization": f"Bearer {token}"}
        )

        self.assertEqual(response.status_code, 200)

    def test_create_ride(self):
        """Test ride creation endpoint."""
        # Create test user and driver
        self.create_test_user()
        self.create_test_driver()

        # Get auth token
        auth_response = self.client.post(
            "/auth/login",
            data=json.dumps(
                {"phone_number": "+1234567890", "password": "TestPass123!"}
            ),
            content_type="application/json",
        )
        token = json.loads(auth_response.data)["token"]

        # Create ride request
        ride_data = {
            "pickup_latitude": 40.7128,
            "pickup_longitude": -74.0060,
            "dropoff_latitude": 40.7589,
            "dropoff_longitude": -73.9851,
            "pickup_time": "2025-01-09T18:29:31",
        }

        response = self.client.post(
            "/rides/create",
            data=json.dumps(ride_data),
            headers={"Authorization": f"Bearer {token}"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertIn("id", response_data)
        self.assertEqual(response_data["status"], "requested")

    def test_update_profile(self):
        """Test profile update endpoint."""
        # Create test user and get token
        self.create_test_user()
        auth_response = self.client.post(
            "/auth/login",
            data=json.dumps(
                {"phone_number": "+1234567890", "password": "TestPass123!"}
            ),
            content_type="application/json",
        )
        token = json.loads(auth_response.data)["token"]

        # Update profile
        update_data = {"name": "Updated Name", "email": "updated@example.com"}
        response = self.client.put(
            "/user/profile",
            data=json.dumps(update_data),
            headers={"Authorization": f"Bearer {token}"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        json_data = json.loads(response.data)
        self.assertEqual(json_data["name"], "Updated Name")
        self.assertEqual(json_data["email"], "updated@example.com")


if __name__ == "__main__":
    unittest.main()
