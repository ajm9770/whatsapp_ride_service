# WhatsApp Ride Service

A ride-hailing service that operates through WhatsApp, connecting passengers with nearby drivers.

## Features

- Request rides through WhatsApp messages
- Automatic driver matching based on proximity
- Real-time notifications for both drivers and passengers
- User authentication and account management
- Secure payment processing with Stripe
- Simple coordinate-based location system
- SQLite database for storing ride and driver information

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your credentials:
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=your_whatsapp_number
DATABASE_URL=sqlite:///rides.db
JWT_SECRET_KEY=your_jwt_secret
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
```

## Usage

### For Passengers
Send a WhatsApp message to the service number in this format:
```
ride pickup_latitude,pickup_longitude to destination_latitude,destination_longitude
```

Example:
```
ride 40.7128,-74.0060 to 40.7589,-73.9851
```

### For Drivers
1. Drivers need to be registered in the system first
2. When a ride request comes in, drivers receive a notification
3. To accept a ride, reply with:
```
accept [ride_id]
```

## API Endpoints

### Authentication
- POST `/api/register`: Register a new user
  ```json
  {
    "phone_number": "+1234567890",
    "password": "securepassword",
    "name": "John Doe",
    "email": "john@example.com"
  }
  ```

- POST `/api/login`: Login and get authentication token
  ```json
  {
    "phone_number": "+1234567890",
    "password": "securepassword"
  }
  ```

### Webhooks
- POST `/webhook`: Twilio WhatsApp webhook
- POST `/webhook/stripe`: Stripe payment webhook

## Payment Flow

1. User requests a ride through WhatsApp
2. System calculates fare based on distance
3. When a driver accepts the ride, passenger receives a payment link
4. After successful payment, both parties are notified
5. Driver can proceed to pickup location

## Pricing

- Base fare: $5.00
- Rate per kilometer: $1.50

## Requirements

- Python 3.8+
- Twilio Account
- WhatsApp Business API access through Twilio
- Internet connection for the server
- Stripe Account

## Note

This is a basic implementation. For production use, consider adding:
- Error handling
- Rate limiting
- Security features
