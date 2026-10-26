from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models.user import User
from app.models.slot import ParkingSlot
from app.models.pricing import PricingRule
from app.models.booking import Booking
from app.models.session import ParkingSession
from app.models.payment import Payment
from app.models.notification import Notification, BarrierAuditLog

__all__ = [
    'db',
    'User',
    'ParkingSlot',
    'PricingRule',
    'Booking',
    'ParkingSession',
    'Payment',
    'Notification',
    'BarrierAuditLog'
]
