import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import db, User, ParkingSlot, PricingRule, Booking, ParkingSession, Payment, Notification, BarrierAuditLog
from app.services.booking_service import BookingService


def seed_database():
    app = create_app()
    with app.app_context():
        print("[*] Seeding Smart Parking Database...")

        # 1. Create Default Users if they don't exist
        admin = User.query.filter_by(email='admin@smartpark.com').first()
        if not admin:
            admin = User(
                full_name='System Administrator',
                email='admin@smartpark.com',
                phone='+91 9876543210',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)

        attendant = User.query.filter_by(email='attendant@smartpark.com').first()
        if not attendant:
            attendant = User(
                full_name='Gate Attendant 1',
                email='attendant@smartpark.com',
                phone='+91 9876543211',
                role='attendant'
            )
            attendant.set_password('staff123')
            db.session.add(attendant)

        customer = User.query.filter_by(email='customer@example.com').first()
        if not customer:
            customer = User(
                full_name='Rahul Sharma',
                email='customer@example.com',
                phone='+91 9876543212',
                role='customer'
            )
            customer.set_password('user123')
            db.session.add(customer)

        db.session.commit()
        print("[OK] Users seeded.")

        # 2. Seed Pricing Rules
        rules_data = [
            {'vehicle_type': '4-wheeler', 'base_hours': 4, 'base_rate': 50.00, 'hourly_rate': 20.00, 'grace': 15},
            {'vehicle_type': '2-wheeler', 'base_hours': 4, 'base_rate': 20.00, 'hourly_rate': 10.00, 'grace': 15},
            {'vehicle_type': 'ev', 'base_hours': 4, 'base_rate': 40.00, 'hourly_rate': 15.00, 'grace': 15}
        ]
        for r in rules_data:
            existing_rule = PricingRule.query.filter_by(vehicle_type=r['vehicle_type']).first()
            if not existing_rule:
                rule = PricingRule(
                    vehicle_type=r['vehicle_type'],
                    base_hours=r['base_hours'],
                    base_rate=Decimal(str(r['base_rate'])),
                    hourly_rate_after_base=Decimal(str(r['hourly_rate'])),
                    grace_period_minutes=r['grace'],
                    is_active=True
                )
                db.session.add(rule)
        db.session.commit()
        print("[OK] Pricing rules seeded.")

        # 3. Seed Parking Slots across floors & zones
        slot_definitions = [
            # Ground Floor - Zone A (Cars)
            ('G-01', 'Ground Floor - Zone A', '4-wheeler', False),
            ('G-02', 'Ground Floor - Zone A', '4-wheeler', False),
            ('G-03', 'Ground Floor - Zone A', '4-wheeler', False),
            ('G-04', 'Ground Floor - Zone A', '4-wheeler', False),
            ('G-05', 'Ground Floor - Zone A', '4-wheeler', False),
            ('G-06', 'Ground Floor - Zone A', '4-wheeler', False),
            # Ground Floor - EV Fast Charging Bay
            ('EV-01', 'Ground Floor - EV Bay', 'ev', True),
            ('EV-02', 'Ground Floor - EV Bay', 'ev', True),
            ('EV-03', 'Ground Floor - EV Bay', 'ev', True),
            ('EV-04', 'Ground Floor - EV Bay', 'ev', True),
            # Basement - Two-Wheeler Bay
            ('B-01', 'Basement - 2-Wheeler Bay', '2-wheeler', False),
            ('B-02', 'Basement - 2-Wheeler Bay', '2-wheeler', False),
            ('B-03', 'Basement - 2-Wheeler Bay', '2-wheeler', False),
            ('B-04', 'Basement - 2-Wheeler Bay', '2-wheeler', False),
            ('B-05', 'Basement - 2-Wheeler Bay', '2-wheeler', False),
            ('B-06', 'Basement - 2-Wheeler Bay', '2-wheeler', False),
            # First Floor - Zone C (Cars)
            ('F1-01', 'Floor 1 - Zone C', '4-wheeler', False),
            ('F1-02', 'Floor 1 - Zone C', '4-wheeler', False),
            ('F1-03', 'Floor 1 - Zone C', '4-wheeler', False),
            ('F1-04', 'Floor 1 - Zone C', '4-wheeler', False),
            ('F1-05', 'Floor 1 - Zone C', '4-wheeler', False),
            ('F1-06', 'Floor 1 - Zone C', '4-wheeler', False),
        ]

        for s_num, zone, v_type, is_ev in slot_definitions:
            if not ParkingSlot.query.filter_by(slot_number=s_num).first():
                slot = ParkingSlot(
                    slot_number=s_num,
                    floor_zone=zone,
                    vehicle_type=v_type,
                    is_ev=is_ev,
                    status='AVAILABLE'
                )
                db.session.add(slot)
        db.session.commit()
        print("[OK] Parking slots seeded.")

        # 4. Seed sample active booking & session for immediate testing
        demo_code = 'PRK-DEMO-001'
        if not Booking.query.filter_by(booking_code=demo_code).first():
            demo_slot = ParkingSlot.query.filter_by(slot_number='G-01').first()
            if demo_slot:
                now = datetime.utcnow()
                booking = Booking(
                    booking_code=demo_code,
                    user_id=customer.id if customer else None,
                    vehicle_number='MH12AB1234',
                    vehicle_type='4-wheeler',
                    slot_id=demo_slot.id,
                    customer_name='Rahul Sharma',
                    customer_phone='+91 9876543212',
                    customer_email='customer@example.com',
                    expected_start_time=now - timedelta(hours=2),
                    expected_end_time=now + timedelta(hours=2),
                    base_hours=4,
                    base_amount=Decimal('50.00'),
                    status='ACTIVE',
                    qr_token=f"SMARTPARK:{demo_code}:MH12AB1234",
                    created_at=now - timedelta(hours=2)
                )
                db.session.add(booking)
                db.session.flush()

                demo_slot.status = 'OCCUPIED'
                demo_slot.current_booking_id = booking.id

                # Payment record
                payment = Payment(
                    booking_id=booking.id,
                    payment_type='PREPAID',
                    amount=Decimal('50.00'),
                    payment_method='UPI',
                    transaction_ref=f"TXN-{now.strftime('%Y%m%d')}-DEMO1",
                    gateway_status='SUCCESS',
                    payment_time=now - timedelta(hours=2)
                )
                db.session.add(payment)

                # Active session
                session = ParkingSession(
                    booking_id=booking.id,
                    slot_id=demo_slot.id,
                    vehicle_number='MH12AB1234',
                    entry_time=now - timedelta(hours=2),
                    prepaid_amount=Decimal('50.00'),
                    extra_amount=Decimal('0.00'),
                    total_amount=Decimal('50.00'),
                    status='IN_PROGRESS'
                )
                db.session.add(session)

                # Barrier audit log
                audit = BarrierAuditLog(
                    gate_type='ENTRY',
                    vehicle_number='MH12AB1234',
                    booking_code=demo_code,
                    action='OPEN',
                    reason='Verified prepaid booking entry authorized',
                    operator_name='Auto Gate Terminal',
                    timestamp=now - timedelta(hours=2)
                )
                db.session.add(audit)

                # Notification
                notif = Notification(
                    booking_id=booking.id,
                    user_id=customer.id if customer else None,
                    title="Vehicle Entry Authorized",
                    message="Vehicle MH12AB1234 entered parking at Gate 1. Slot: G-01.",
                    notification_type="INFO",
                    channel="IN_APP",
                    sent_at=now - timedelta(hours=2)
                )
                db.session.add(notif)

                db.session.commit()
                print("[OK] Sample active booking & session seeded (MH12AB1234 / PRK-DEMO-001).")

        print("[SUCCESS] Database seeding finished successfully!")


if __name__ == '__main__':
    seed_database()
