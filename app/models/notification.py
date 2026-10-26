from datetime import datetime
from app.models import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(20), default='INFO', nullable=False)  # INFO, WARNING, ALERT, SUCCESS
    channel = db.Column(db.String(20), default='IN_APP', nullable=False)  # IN_APP, SMS, EMAIL
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'booking_id': self.booking_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'channel': self.channel,
            'is_read': self.is_read,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


class BarrierAuditLog(db.Model):
    __tablename__ = 'barrier_audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    gate_type = db.Column(db.String(10), nullable=False)  # ENTRY, EXIT
    vehicle_number = db.Column(db.String(20), nullable=False)
    booking_code = db.Column(db.String(32), nullable=True)
    action = db.Column(db.String(20), nullable=False)  # OPEN, DENY, MANUAL_OVERRIDE
    reason = db.Column(db.String(255), nullable=False)
    operator_name = db.Column(db.String(100), default='System Automated', nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'gate_type': self.gate_type,
            'vehicle_number': self.vehicle_number,
            'booking_code': self.booking_code,
            'action': self.action,
            'reason': self.reason,
            'operator_name': self.operator_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
