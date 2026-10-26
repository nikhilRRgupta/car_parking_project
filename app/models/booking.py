from datetime import datetime
from app.models import db


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_code = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    vehicle_number = db.Column(db.String(20), nullable=False, index=True)
    vehicle_type = db.Column(db.String(20), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slots.id'), nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    expected_start_time = db.Column(db.DateTime, nullable=False)
    expected_end_time = db.Column(db.DateTime, nullable=False)
    base_hours = db.Column(db.Integer, default=4, nullable=False)
    base_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(
        db.String(20),
        default='PENDING_PAYMENT',
        nullable=False,
        index=True
    )  # PENDING_PAYMENT, CONFIRMED, ACTIVE, COMPLETED, CANCELLED, EXPIRED
    qr_token = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)  # Reservation hold expiry timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    payments = db.relationship('Payment', backref='booking', lazy=True, cascade='all, delete-orphan')
    session = db.relationship('ParkingSession', backref='booking', uselist=False, lazy=True, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='booking', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'booking_code': self.booking_code,
            'vehicle_number': self.vehicle_number,
            'vehicle_type': self.vehicle_type,
            'slot_id': self.slot_id,
            'slot_number': self.slot.slot_number if self.slot else None,
            'floor_zone': self.slot.floor_zone if self.slot else None,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'customer_email': self.customer_email,
            'expected_start_time': self.expected_start_time.isoformat() if self.expected_start_time else None,
            'expected_end_time': self.expected_end_time.isoformat() if self.expected_end_time else None,
            'base_hours': self.base_hours,
            'base_amount': float(self.base_amount),
            'status': self.status,
            'qr_token': self.qr_token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
