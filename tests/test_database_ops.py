"""Test suite for database operations."""

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from whatsapp_ride_service.auth import UserManager
from whatsapp_ride_service.database_ops import DatabaseOps
from whatsapp_ride_service.models import Base, User, Driver, Ride, Payment
import os


class TestDatabaseOps(unittest.TestCase):
    """Test cases for database operations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_counter = 0  # Initialize counter for unique phone numbers

    @classmethod
    def setUpClass(cls):
        # Use SQLite for testing
        cls.engine = create_engine("sqlite:///test_db_ops.db")
        Base.metadata.create_all(cls.engine)
        Session = sessionmaker(bind=cls.engine)
        cls.session = Session()
        cls.db_ops = DatabaseOps(cls.session)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        Base.metadata.drop_all(cls.engine)
        if os.path.exists("test_db_ops.db"):
            os.remove("test_db_ops.db")

    def setUp(self):
        """Set up test environment."""
        # Clear all tables before each test
        try:
            self.session.query(Payment).delete()
            self.session.query(Ride).delete()
            self.session.query(User).delete()
            self.session.query(Driver).delete()
            self.session.commit()
        except:
            self.session.rollback()
            raise

    def create_test_user(self):
        user_manager = UserManager(self.session)
        return user_manager.create_user(
            name="Test User",
            email="test@example.com",
            phone_number="+1234567890",
            password="TestPass123!",
        )

    def create_test_driver(self, latitude=40.7128, longitude=-74.0060):
        # Generate a unique phone number for each test driver
        driver = Driver(
            name="Test Driver",
            phone_number=f"+1987654{self.driver_counter:04d}",  # Use counter to make unique numbers
            current_latitude=latitude,
            current_longitude=longitude,
            is_available=True,
        )
        self.driver_counter += 1  # Increment counter for next driver
        self.session.add(driver)
        self.session.commit()
        return driver

    def create_test_ride(self, user, driver, status="completed"):
        ride = Ride(
            user_id=user.id,
            driver_id=driver.id,
            pickup_latitude=40.7128,
            pickup_longitude=-74.0060,
            dropoff_latitude=40.7589,
            dropoff_longitude=-73.9851,
            status=status,
            completed_at=datetime.utcnow() if status == "completed" else None,
        )
        self.session.add(ride)
        self.session.commit()
        return ride

    def create_test_payment(self, ride, amount=25.0, status="completed"):
        payment = Payment(
            ride_id=ride.id,
            user_id=ride.user_id,  # Set the user_id from the ride
            amount=amount,
            status=status,
        )
        self.session.add(payment)
        self.session.commit()
        return payment

    def test_get_available_drivers(self):
        # Create drivers at different locations
        driver1 = self.create_test_driver(40.7128, -74.0060)  # NYC
        driver2 = self.create_test_driver(34.0522, -118.2437)  # LA

        # Search for drivers near NYC
        drivers = self.db_ops.get_available_drivers(40.7128, -74.0060, radius_km=10)
        self.assertEqual(len(drivers), 1)
        self.assertEqual(drivers[0].id, driver1.id)

    def test_get_user_ride_history(self):
        # Create test user and driver
        user = self.create_test_user()
        driver = self.create_test_driver()

        # Create some rides
        ride1 = self.create_test_ride(user, driver)
        ride2 = self.create_test_ride(user, driver)

        # Get ride history
        rides_with_payments = self.db_ops.get_user_ride_history(user.id)
        self.assertEqual(len(rides_with_payments), 2)

        # Most recent first
        ride, payment = rides_with_payments[0]
        self.assertEqual(ride.id, ride2.id)

        ride, payment = rides_with_payments[1]
        self.assertEqual(ride.id, ride1.id)

    def test_get_driver_earnings(self):
        # Create test user and driver
        user = self.create_test_user()
        driver = self.create_test_driver()

        # Create rides with payments
        ride1 = self.create_test_ride(user, driver)
        payment1 = self.create_test_payment(ride1, amount=25.0)

        ride2 = self.create_test_ride(user, driver)
        payment2 = self.create_test_payment(ride2, amount=30.0)

        # Get driver earnings
        earnings = self.db_ops.get_driver_earnings(driver.id)
        self.assertEqual(earnings, 55.0)  # 25.0 + 30.0

    def test_get_active_rides(self):
        # Create test user and driver
        user = self.create_test_user()
        driver = self.create_test_driver()

        # Create rides with different statuses
        ride1 = self.create_test_ride(user, driver, status="in_progress")
        ride2 = self.create_test_ride(user, driver, status="completed")

        # Get active rides
        active_rides = self.db_ops.get_active_rides()
        self.assertEqual(len(active_rides), 1)
        self.assertEqual(active_rides[0].id, ride1.id)

    def test_get_user_stats(self):
        # Create test user and driver
        user = self.create_test_user()
        driver = self.create_test_driver()

        # Create completed rides with payments
        ride1 = self.create_test_ride(user, driver, status="completed")
        payment1 = self.create_test_payment(ride1, amount=25.0)

        ride2 = self.create_test_ride(user, driver, status="completed")
        payment2 = self.create_test_payment(ride2, amount=30.0)

        # Create an in-progress ride
        ride3 = self.create_test_ride(user, driver, status="in_progress")

        # Get user stats
        stats = self.db_ops.get_user_stats(user.id)
        self.assertEqual(stats["total_rides"], 3)
        self.assertEqual(stats["completed_rides"], 2)
        self.assertEqual(stats["total_spent"], 55.0)

    def test_update_driver_location(self):
        # Create test driver
        driver = self.create_test_driver()

        # Update location
        new_lat = 40.7589
        new_lng = -73.9851
        self.db_ops.update_driver_location(driver.id, new_lat, new_lng)

        # Verify location was updated
        updated_driver = self.session.get(Driver, driver.id)  # Updated to session.get()
        self.assertEqual(updated_driver.current_latitude, new_lat)
        self.assertEqual(updated_driver.current_longitude, new_lng)


if __name__ == "__main__":
    unittest.main()
