from datetime import datetime
from app.models import db


class PricingRule(db.Model):
    __tablename__ = 'pricing_rules'

    id = db.Column(db.Integer, primary_key=True)
    vehicle_type = db.Column(db.String(20), unique=True, nullable=False)  # '2-wheeler', '4-wheeler', 'ev'
    base_hours = db.Column(db.Integer, default=4, nullable=False)
    base_rate = db.Column(db.Numeric(10, 2), nullable=False)  # e.g., ₹50.00
    hourly_rate_after_base = db.Column(db.Numeric(10, 2), nullable=False)  # e.g., ₹20.00
    grace_period_minutes = db.Column(db.Integer, default=15, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_type': self.vehicle_type,
            'base_hours': self.base_hours,
            'base_rate': float(self.base_rate),
            'hourly_rate_after_base': float(self.hourly_rate_after_base),
            'grace_period_minutes': self.grace_period_minutes,
            'is_active': self.is_active,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
