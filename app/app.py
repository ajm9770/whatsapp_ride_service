from flask import Flask, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Driver, Ride, User, Payment
from datetime import datetime
import config
from geopy.distance import geodesic
import json
import stripe
import jwt
from functools import wraps
import phonenumbers

app = Flask(__name__)
stripe.api_key = config.STRIPE_SECRET_KEY

# Initialize Twilio client
client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

# Initialize database
engine = create_engine(config.DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.split()[1]  # Remove 'Bearer ' prefix
            data = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
            session = Session()
            current_user = session.query(User).get(data['user_id'])
            session.close()
            if not current_user:
                return jsonify({'message': 'Invalid token'}), 401
        except:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def calculate_fare(pickup_coords, dest_coords):
    distance = geodesic(pickup_coords, dest_coords).kilometers
    return config.BASE_FARE + (distance * config.RATE_PER_KM)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    required_fields = ['phone_number', 'password', 'name', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    try:
        # Validate phone number
        phone_number = phonenumbers.parse(data['phone_number'], None)
        if not phonenumbers.is_valid_number(phone_number):
            return jsonify({'message': 'Invalid phone number'}), 400
        
        session = Session()
        
        # Check if user already exists
        if session.query(User).filter_by(phone_number=data['phone_number']).first():
            return jsonify({'message': 'Phone number already registered'}), 400
        
        if session.query(User).filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already registered'}), 400
        
        # Create Stripe customer
        stripe_customer = stripe.Customer.create(
            phone=data['phone_number'],
            email=data['email'],
            name=data['name']
        )
        
        # Create user
        user = User(
            phone_number=data['phone_number'],
            name=data['name'],
            email=data['email'],
            stripe_customer_id=stripe_customer.id
        )
        user.set_password(data['password'])
        
        session.add(user)
        session.commit()
        
        token = user.generate_token()
        session.close()
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token
        }), 201
        
    except Exception as e:
        session.rollback()
        return jsonify({'message': str(e)}), 400

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('phone_number') or not data.get('password'):
        return jsonify({'message': 'Missing credentials'}), 400
    
    session = Session()
    user = session.query(User).filter_by(phone_number=data['phone_number']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = user.generate_token()
    session.close()
    
    return jsonify({'token': token})

def find_nearest_driver(latitude, longitude):
    session = Session()
    nearest_driver = None
    min_distance = float('inf')
    
    available_drivers = session.query(Driver).filter_by(is_available=True).all()
    for driver in available_drivers:
        distance = geodesic(
            (latitude, longitude),
            (driver.current_latitude, driver.current_longitude)
        ).km
        
        if distance < config.MAX_SEARCH_RADIUS_KM and distance < min_distance:
            min_distance = distance
            nearest_driver = driver
    
    session.close()
    return nearest_driver

def process_ride_request(user_id, message_body):
    try:
        # Expected format: "ride pickup_lat,pickup_long to dest_lat,dest_long"
        parts = message_body.lower().split('to')
        if len(parts) != 2:
            return "Please use the format: ride pickup_lat,pickup_long to dest_lat,dest_long"
        
        pickup_coords = [float(x.strip()) for x in parts[0].replace('ride', '').strip().split(',')]
        dest_coords = [float(x.strip()) for x in parts[1].strip().split(',')]
        
        nearest_driver = find_nearest_driver(pickup_coords[0], pickup_coords[1])
        
        if not nearest_driver:
            return "Sorry, no drivers are currently available in your area."
        
        session = Session()
        
        # Calculate fare
        fare = calculate_fare((pickup_coords[0], pickup_coords[1]), (dest_coords[0], dest_coords[1]))
        
        # Create ride record
        ride = Ride(
            passenger_id=user_id,
            driver_id=nearest_driver.id,
            pickup_latitude=pickup_coords[0],
            pickup_longitude=pickup_coords[1],
            destination_latitude=dest_coords[0],
            destination_longitude=dest_coords[1]
        )
        session.add(ride)
        session.flush()
        
        # Create payment record
        user = session.query(User).get(user_id)
        payment_intent = stripe.PaymentIntent.create(
            amount=int(fare * 100),  # Convert to cents
            currency=config.CURRENCY,
            customer=user.stripe_customer_id,
            metadata={'ride_id': ride.id}
        )
        
        payment = Payment(
            ride_id=ride.id,
            amount=fare,
            stripe_payment_intent_id=payment_intent.id
        )
        session.add(payment)
        
        nearest_driver.is_available = False
        session.commit()
        
        # Notify driver
        driver_message = (
            f"New ride request!\n"
            f"Pickup: {pickup_coords[0]}, {pickup_coords[1]}\n"
            f"Destination: {dest_coords[0]}, {dest_coords[1]}\n"
            f"Fare: ${fare:.2f}\n"
            f"Reply 'accept {ride.id}' to accept this ride"
        )
        
        client.messages.create(
            from_=f'whatsapp:{config.TWILIO_WHATSAPP_NUMBER}',
            to=f'whatsapp:{nearest_driver.phone_number}',
            body=driver_message
        )
        
        session.close()
        return (
            f"Looking for a driver... We'll notify you when one accepts your ride!\n"
            f"Estimated fare: ${fare:.2f}"
        )
        
    except Exception as e:
        return f"Error processing your request: {str(e)}"

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        session = Session()
        payment = session.query(Payment).filter_by(
            stripe_payment_intent_id=payment_intent.id
        ).first()
        
        if payment:
            payment.status = 'completed'
            session.commit()
            
            # Notify both parties
            ride = payment.ride
            messages = [
                (ride.passenger.phone_number, "Your payment has been processed successfully!"),
                (ride.driver.phone_number, f"Payment of ${payment.amount:.2f} has been received for the ride.")
            ]
            
            for phone_number, message in messages:
                client.messages.create(
                    from_=f'whatsapp:{config.TWILIO_WHATSAPP_NUMBER}',
                    to=f'whatsapp:{phone_number}',
                    body=message
                )
        
        session.close()
    
    return jsonify({'status': 'success'}), 200

@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    sender = request.values.get('From', '').replace('whatsapp:', '')
    
    session = Session()
    user = session.query(User).filter_by(phone_number=sender).first()
    
    if not user:
        session.close()
        return str(MessagingResponse().message(
            "Please register first through our app to use this service."
        ))
    
    resp = MessagingResponse()
    
    if incoming_msg.startswith('ride'):
        response_message = process_ride_request(user.id, incoming_msg)
    elif incoming_msg.startswith('accept'):
        # Handle driver accepting ride
        try:
            ride_id = int(incoming_msg.split()[1])
            ride = session.query(Ride).get(ride_id)
            if ride and ride.status == 'requested':
                ride.status = 'accepted'
                session.commit()
                
                # Send payment link to passenger
                payment = ride.payment
                payment_link = stripe.PaymentLink.create(
                    payment_intent=payment.stripe_payment_intent_id
                )
                
                client.messages.create(
                    from_=f'whatsapp:{config.TWILIO_WHATSAPP_NUMBER}',
                    to=f'whatsapp:{ride.passenger.phone_number}',
                    body=f"Your ride has been accepted! Please complete the payment: {payment_link.url}"
                )
                response_message = "You've accepted the ride. Please proceed to pickup location once payment is confirmed."
            else:
                response_message = "This ride is no longer available."
        except Exception as e:
            response_message = f"Error accepting ride: {str(e)}"
    else:
        response_message = (
            "Welcome to WhatsApp Ride Service!\n"
            "To request a ride, send: ride pickup_lat,pickup_long to dest_lat,dest_long"
        )
    
    session.close()
    resp.message(response_message)
    return str(resp)

if __name__ == '__main__':
    app.run(debug=True)
