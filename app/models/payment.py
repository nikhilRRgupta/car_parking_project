from datetime import datetime
from app.models import db


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('parking_sessions.id', ondelete='SET NULL'), nullable=True)
    payment_type = db.Column(db.String(20), nullable=False)  # PREPAID, EXIT_OVERSTAY
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # CARD, UPI, NET_BANKING, CASH_KIOSK
    transaction_ref = db.Column(db.String(64), unique=True, nullable=False, index=True)
    gateway_status = db.Column(db.String(20), default='SUCCESS', nullable=False)  # SUCCESS, FAILED, PENDING
    payment_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'booking_id': self.booking_id,
            'session_id': self.session_id,
            'payment_type': self.payment_type,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'transaction_ref': self.transaction_ref,
            'gateway_status': self.gateway_status,
            'payment_time': self.payment_time.isoformat() if self.payment_time else None
        }
