from datetime import datetime, timedelta
from app.models import db, ParkingSlot, Booking
from app.services.booking_service import BookingService


def test_double_booking_prevention(app):
    with app.app_context():
        slot = ParkingSlot.query.filter_by(slot_number='TEST-G01').first()

        # User 1 reserves the slot
        res1 = BookingService.reserve_slot_concurrency_safe(
            slot_id=slot.id,
            vehicle_number='KA01AA1111',
            vehicle_type='4-wheeler',
            customer_name='User One',
            customer_phone='9999999991',
            customer_email='user1@test.com'
        )
        assert res1['success'] is True
        assert res1['slot_number'] == 'TEST-G01'

        # Slot is now RESERVED
        assert slot.status == 'RESERVED'

        # User 2 attempts to reserve the exact same slot at the same time
        res2 = BookingService.reserve_slot_concurrency_safe(
            slot_id=slot.id,
            vehicle_number='KA02BB2222',
            vehicle_type='4-wheeler',
            customer_name='User Two',
            customer_phone='9999999992',
            customer_email='user2@test.com'
        )
        assert res2['success'] is False
        assert 'is no longer available' in res2['message']


def test_unpaid_reservation_auto_expiry(app):
    with app.app_context():
        slot = ParkingSlot.query.filter_by(slot_number='TEST-B01').first()

        # Reserve slot
        res = BookingService.reserve_slot_concurrency_safe(
            slot_id=slot.id,
            vehicle_number='DL01XY9999',
            vehicle_type='2-wheeler',
            customer_name='Bike Rider',
            customer_phone='9888888888',
            customer_email='biker@test.com'
        )
        assert res['success'] is True
        booking = Booking.query.get(res['booking_id'])

        # Manually backdate expiry to simulate 10 minutes elapsed without payment
        booking.expires_at = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

        # Run cleanup sweeper
        cleaned_count = BookingService.cleanup_expired_reservations()
        assert cleaned_count >= 1

        # Booking must now be EXPIRED and slot released back to AVAILABLE
        db.session.refresh(booking)
        db.session.refresh(slot)
        assert booking.status == 'EXPIRED'
        assert slot.status == 'AVAILABLE'
