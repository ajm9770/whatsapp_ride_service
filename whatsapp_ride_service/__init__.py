"""WhatsApp Ride Service Application"""

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from .models import Base

def create_app(config_object=None):
    app = Flask(__name__)
    
    # Load config
    if config_object:
        app.config.from_object(config_object)
    
    # Initialize database
    engine = create_engine(app.config.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///whatsapp_ride.db'))
    Base.metadata.create_all(engine)
    
    # Create scoped session
    session_factory = sessionmaker(bind=engine)
    Session = scoped_session(session_factory)
    app.db_session = Session
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        Session.remove()
    
    # Register routes
    from .routes import auth_routes, user_routes, ride_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(ride_routes.bp)
    
    return app
