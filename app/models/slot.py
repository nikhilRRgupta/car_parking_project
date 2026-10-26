from datetime import datetime
from app.models import db


class ParkingSlot(db.Model):
    __tablename__ = 'parking_slots'

    id = db.Column(db.Integer, primary_key=True)
    slot_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    floor_zone = db.Column(db.String(50), nullable=False)  # e.g., 'Ground Floor - Zone A', 'Floor 1', 'EV Bay'
    vehicle_type = db.Column(db.String(20), nullable=False)  # '2-wheeler', '4-wheeler', 'ev'
    is_ev = db.Column(db.Boolean, default=False, nullable=False)
    status = db.Column(db.String(20), default='AVAILABLE', nullable=False, index=True)  # AVAILABLE, RESERVED, OCCUPIED, MAINTENANCE
    current_booking_id = db.Column(db.Integer, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='slot', lazy=True)
    sessions = db.relationship('ParkingSession', backref='slot', lazy=True)

    @property
    def is_available(self) -> bool:
        return self.status == 'AVAILABLE'

    def to_dict(self):
        return {
            'id': self.id,
            'slot_number': self.slot_number,
            'floor_zone': self.floor_zone,
            'vehicle_type': self.vehicle_type,
            'is_ev': self.is_ev,
            'status': self.status,
            'current_booking_id': self.current_booking_id,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
