"""Database Migration Script"""
import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from whatsapp_ride_service.models import Base


def migrate_database():
    """Recreate database with new schema"""
    # Remove existing database file
    db_file = "whatsapp_ride.db"
    if os.path.exists(db_file):
        os.remove(db_file)

    # Create new database with updated schema
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(engine)

    print("Database schema updated successfully!")


if __name__ == "__main__":
    migrate_database()
