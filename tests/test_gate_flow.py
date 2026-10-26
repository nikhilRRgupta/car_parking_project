from datetime import datetime, timedelta
from app.models import db, ParkingSlot, Booking, ParkingSession
from app.services.booking_service import BookingService
from app.services.gate_service import GateService


def test_complete_gate_entry_and_exit_flow(app):
    with app.app_context():
        slot = ParkingSlot.query.filter_by(slot_number='TEST-G01').first()

        # Step 1: Online Slot Reservation
        res = BookingService.reserve_slot_concurrency_safe(
            slot_id=slot.id,
            vehicle_number='MH02CD5678',
            vehicle_type='4-wheeler',
            customer_name='Amit Verma',
            customer_phone='9876543210',
            customer_email='amit@test.com'
        )
        assert res['success'] is True
        booking_id = res['booking_id']
        booking_code = res['booking_code']

        # Step 2: Attempt Entry before payment -> Must DENY
        entry_deny = GateService.validate_and_authorize_entry(booking_code, vehicle_plate='MH02CD5678')
        assert entry_deny['success'] is False
        assert 'Payment pending' in entry_deny['message']

        # Step 3: Verified Online Payment
        pay_res = BookingService.confirm_booking_payment(booking_id, payment_method='UPI')
        assert pay_res['success'] is True

        # Step 4: Authorize Gate Entry
        entry_auth = GateService.validate_and_authorize_entry(booking_code, vehicle_plate='MH02CD5678')
        assert entry_auth['success'] is True
        assert entry_auth['barrier_action'] == 'OPEN'

        # Check slot is now OCCUPIED
        db.session.refresh(slot)
        assert slot.status == 'OCCUPIED'

        # Active session exists
        session = ParkingSession.query.filter_by(booking_id=booking_id).first()
        assert session is not None
        assert session.status == 'IN_PROGRESS'

        # Step 5: Check Exit Bill (Normal stay within 4 hours)
        bill_res = GateService.prepare_exit_bill(booking_code)
        assert bill_res['success'] is True
        assert bill_res['bill']['balance_due'] == 0.0

        # Step 6: Complete Exit & Release Slot
        exit_res = GateService.complete_exit(session.id, payment_method='PREPAID')
        assert exit_res['success'] is True
        assert exit_res['barrier_action'] == 'OPEN'

        # Slot must now be genuinely released back to AVAILABLE
        db.session.refresh(slot)
        assert slot.status == 'AVAILABLE'
        assert slot.current_booking_id is None
