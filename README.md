# WhatsApp Ride Service

A ride-hailing service that operates through WhatsApp, making it accessible to users without smartphones or dedicated apps.

## Features

- User registration and authentication via WhatsApp
- Ride booking and status tracking
- Real-time driver location updates
- Secure payment processing
- Rating system for both drivers and passengers

## Prerequisites

- Python 3.9+
- SQLite
- Twilio account for WhatsApp integration
- Stripe account for payment processing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/whatsapp_ride_service.git
cd whatsapp_ride_service
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
STRIPE_SECRET_KEY=your_stripe_key
JWT_SECRET_KEY=your_jwt_secret
```

## Development Setup

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **Flake8**: Code linting
  - flake8-docstrings for docstring checks
  - flake8-import-order for import ordering
  - flake8-quotes for consistent quote usage
- **MyPy**: Static type checking
- **Pytest**: Testing framework with coverage reporting

### Running Tests

```bash
pytest
```

### Code Quality Checks

The following checks run automatically on each commit:

1. Code formatting (black)
2. Linting (flake8)
3. Type checking (mypy)
4. Unit tests (pytest)

To manually run all checks:
```bash
pre-commit run --all-files
```

### Configuration Files

Configuration files for development tools are located in the `admin/` directory:
- `admin/.flake8`: Flake8 configuration
- `admin/mypy.ini`: MyPy configuration
- `admin/pytest.ini`: Pytest configuration

## Running the Application

1. Start the server:
```bash
python -m whatsapp_ride_service
```

2. The service will be available at `http://localhost:5000`

## API Documentation

### Authentication Endpoints
- POST `/auth/register`: Register a new user
- POST `/auth/login`: Login and receive JWT token

### User Endpoints
- GET `/user/profile`: Get user profile
- PUT `/user/profile`: Update user profile
- GET `/user/rides`: Get user's ride history

### Ride Endpoints
- POST `/ride/request`: Request a new ride
- GET `/ride/<ride_id>`: Get ride status
- PUT `/ride/<ride_id>/complete`: Complete a ride
- POST `/ride/<ride_id>/rate`: Rate a completed ride

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
   - Write meaningful commit messages
   - Add tests for new features
   - Update documentation as needed
4. Run all checks (`pre-commit run --all-files`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
