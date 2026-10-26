from datetime import datetime
from app.models import db


class ParkingSession(db.Model):
    __tablename__ = 'parking_sessions'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), unique=True, nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slots.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False, index=True)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    exit_time = db.Column(db.DateTime, nullable=True)
    total_duration_minutes = db.Column(db.Integer, default=0)
    prepaid_amount = db.Column(db.Numeric(10, 2), nullable=False)
    extra_amount = db.Column(db.Numeric(10, 2), default=0.00)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='IN_PROGRESS', nullable=False, index=True)  # IN_PROGRESS, COMPLETED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    payments = db.relationship('Payment', backref='session', lazy=True)

    @property
    def is_in_progress(self) -> bool:
        return self.status == 'IN_PROGRESS'

    def elapsed_minutes(self) -> int:
        end = self.exit_time if self.exit_time else datetime.utcnow()
        delta = end - self.entry_time
        return max(0, int(delta.total_seconds() // 60))

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'slot_id': self.slot_id,
            'slot_number': self.slot.slot_number if self.slot else None,
            'vehicle_number': self.vehicle_number,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'elapsed_minutes': self.elapsed_minutes(),
            'total_duration_minutes': self.total_duration_minutes,
            'prepaid_amount': float(self.prepaid_amount),
            'extra_amount': float(self.extra_amount or 0.0),
            'total_amount': float(self.total_amount),
            'status': self.status
        }
