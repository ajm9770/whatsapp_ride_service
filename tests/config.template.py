"""Test configuration template
Copy this file to config.py and update the values with your test credentials
"""

# Database
SQLALCHEMY_DATABASE_URI = "sqlite:///test.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JWT Configuration
JWT_SECRET_KEY = "your-test-secret-key"
JWT_EXPIRATION_HOURS = 24

# Stripe Configuration
STRIPE_SECRET_KEY = "your-test-stripe-key"
STRIPE_PUBLISHABLE_KEY = "your-test-stripe-publishable-key"

# Twilio Configuration
TWILIO_ACCOUNT_SID = "your-test-account-sid"
TWILIO_AUTH_TOKEN = "your-test-auth-token"
TWILIO_PHONE_NUMBER = "+15555555555"

# Test User Credentials
TEST_USER = {
    "name": "Test User",
    "email": "test@example.com",
    "phone_number": "+1234567890",
    "password": "TestPass123!",
}

# Test Driver Data
TEST_DRIVER = {
    "name": "Test Driver",
    "phone_number": "+1987654321",
    "current_latitude": 40.7128,
    "current_longitude": -74.0060,
}
