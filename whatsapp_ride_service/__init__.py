"""WhatsApp Ride Service application package."""

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .models import Base


def create_app(config_name="development"):
    """Create and configure the Flask application.

    Args:
        config_name: The name of the configuration to use.

    Returns:
        The configured Flask application.
    """
    app = Flask("whatsapp_ride_service")

    # Load config based on environment
    if config_name == "testing":
        app.config.from_object("tests.config.TestingConfig")
    else:
        app.config.from_object("whatsapp_ride_service.config.DevelopmentConfig")

    # Initialize database
    engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    app.db_session = scoped_session(Session)

    # Register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.user_routes import user_bp
    from .routes.ride_routes import ride_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(ride_bp)

    @app.teardown_appcontext
    def cleanup(resp_or_exc):
        """Clean up database session."""
        app.db_session.close()

    return app
