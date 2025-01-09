"""Database operations for common queries"""
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timedelta
from .models import User, Driver, Ride, Payment
from typing import List, Optional, Tuple

class DatabaseOps:
    def __init__(self, session):
        self.session = session

    def get_available_drivers(self, latitude: float, longitude: float, radius_km: float = 5) -> List[Driver]:
        """Get available drivers within radius_km of the given coordinates"""
        # Note: This is a simplified version. In production, you'd want to use
        # proper geographic distance calculations (e.g., PostGIS)
        drivers = self.session.query(Driver).filter(
            and_(
                Driver.is_available == True,
                Driver.current_latitude.between(latitude - (radius_km/111), latitude + (radius_km/111)),
                Driver.current_longitude.between(longitude - (radius_km/111), longitude + (radius_km/111))
            )
        ).all()
        return drivers

    def get_user_ride_history(self, user_id: int, limit: int = 10) -> List[Tuple[Ride, Optional[Payment]]]:
        """Get user's ride history with payment information"""
        rides_with_payments = self.session.query(Ride, Payment).\
            outerjoin(Payment).\
            filter(Ride.user_id == user_id).\
            order_by(desc(Ride.created_at)).\
            limit(limit).\
            all()
        return rides_with_payments

    def get_driver_earnings(self, driver_id: int, days: int = 30) -> float:
        """Calculate driver's earnings for the last n days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        earnings = self.session.query(Payment).\
            join(Ride).\
            filter(
                and_(
                    Ride.driver_id == driver_id,
                    Payment.status == 'completed',
                    Payment.created_at >= start_date
                )
            ).\
            with_entities(func.sum(Payment.amount)).\
            scalar()
        return earnings or 0.0

    def get_active_rides(self) -> List[Ride]:
        """Get all currently active rides"""
        return self.session.query(Ride).\
            filter(Ride.status == 'in_progress').\
            all()

    def get_user_stats(self, user_id: int) -> dict:
        """Get user's ride statistics"""
        total_rides = self.session.query(func.count(Ride.id)).\
            filter(Ride.user_id == user_id).\
            scalar() or 0

        completed_rides = self.session.query(func.count(Ride.id)).\
            filter(and_(
                Ride.user_id == user_id,
                Ride.status == 'completed'
            )).\
            scalar() or 0

        total_spent = self.session.query(func.sum(Payment.amount)).\
            join(Ride).\
            filter(and_(
                Ride.user_id == user_id,
                Payment.status == 'completed'
            )).\
            scalar() or 0.0

        return {
            'total_rides': total_rides,
            'completed_rides': completed_rides,
            'total_spent': total_spent
        }

    def update_driver_location(self, driver_id: int, latitude: float, longitude: float) -> Driver:
        """Update driver's current location"""
        driver = self.session.get(Driver, driver_id)  
        if driver:
            driver.current_latitude = latitude
            driver.current_longitude = longitude
            driver.last_updated = datetime.utcnow()
            self.session.commit()
        return driver
