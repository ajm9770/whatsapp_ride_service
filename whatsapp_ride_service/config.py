import os
from dotenv import load_dotenv

load_dotenv()

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///rides.db')

# Ride Configuration
MAX_SEARCH_RADIUS_KM = 10  # Maximum radius to search for drivers
RIDE_REQUEST_TIMEOUT_MINUTES = 5  # Time before a ride request expires

# Authentication Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
JWT_EXPIRATION_HOURS = 24

# Stripe Configuration
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
CURRENCY = 'usd'
BASE_FARE = 5.00  # Base fare in USD
RATE_PER_KM = 1.50  # Rate per kilometer in USD
