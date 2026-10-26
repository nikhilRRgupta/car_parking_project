import os
import sys
from decimal import Decimal
import pytest

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.config import TestingConfig
from app.models import db, ParkingSlot, PricingRule, User


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        # Seed essential pricing rules
        rule_4w = PricingRule(
            vehicle_type='4-wheeler',
            base_hours=4,
            base_rate=Decimal('50.00'),
            hourly_rate_after_base=Decimal('20.00'),
            grace_period_minutes=15,
            is_active=True
        )
        rule_2w = PricingRule(
            vehicle_type='2-wheeler',
            base_hours=4,
            base_rate=Decimal('20.00'),
            hourly_rate_after_base=Decimal('10.00'),
            grace_period_minutes=15,
            is_active=True
        )
        db.session.add_all([rule_4w, rule_2w])

        # Seed test slots
        slot1 = ParkingSlot(
            slot_number='TEST-G01',
            floor_zone='Ground Floor',
            vehicle_type='4-wheeler',
            is_ev=False,
            status='AVAILABLE'
        )
        slot2 = ParkingSlot(
            slot_number='TEST-B01',
            floor_zone='Basement',
            vehicle_type='2-wheeler',
            is_ev=False,
            status='AVAILABLE'
        )
        db.session.add_all([slot1, slot2])

        # Seed admin
        admin = User(
            full_name='Test Admin',
            email='admin@test.com',
            phone='1234567890',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
