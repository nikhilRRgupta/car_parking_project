import io
import base64
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
import qrcode
from app.models import db, ParkingSlot, Booking
from app.services.pricing_service import PricingService
from app.services.payment_service import PaymentService
from app.services.notification_service import NotificationService


class BookingService:
    @staticmethod
    def cleanup_expired_reservations():
        """
        Releases slots held under unpaid reservations that have exceeded the expiry window.
        """
        now = datetime.utcnow()
        expired_bookings = Booking.query.filter(
            Booking.status == 'PENDING_PAYMENT',
            Booking.expires_at < now
        ).all()

        for b in expired_bookings:
            b.status = 'EXPIRED'
            if b.slot and b.slot.status == 'RESERVED':
                b.slot.status = 'AVAILABLE'
                b.slot.current_booking_id = None

        if expired_bookings:
            db.session.commit()
        return len(expired_bookings)

    @staticmethod
    def generate_booking_code() -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:6].upper()
        return f"PRK-{date_str}-{unique_suffix}"

    @staticmethod
    def generate_qr_base64(payload_text: str) -> str:
        """
        Generates a high-quality base64 PNG data URI for the booking QR pass.
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2
        )
        qr.add_data(payload_text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#1e293b", back_color="#ffffff")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"

    @classmethod
    def reserve_slot_concurrency_safe(
        cls,
        slot_id: int,
        vehicle_number: str,
        vehicle_type: str,
        customer_name: str,
        customer_phone: str,
        customer_email: str,
        user_id: int = None,
        duration_hours: int = 4,
        hold_minutes: int = 10
    ) -> dict:
        """
        Safely reserves a slot using row locking/atomic checking to prevent race conditions.
        """
        cls.cleanup_expired_reservations()

        vehicle_number = vehicle_number.strip().upper().replace(" ", "")

        # Atomic check and lock on slot
        slot = ParkingSlot.query.with_for_update().filter_by(id=slot_id).first()

        if not slot:
            return {'success': False, 'message': 'Selected slot does not exist'}

        if slot.status != 'AVAILABLE':
            return {
                'success': False,
                'message': f'Slot {slot.slot_number} is no longer available (currently {slot.status}). Please choose another.'
            }

        # Check vehicle compatibility
        if slot.vehicle_type != vehicle_type and not (vehicle_type == 'ev' and slot.is_ev):
            return {
                'success': False,
                'message': f'Slot {slot.slot_number} is designated for {slot.vehicle_type}, not {vehicle_type}.'
            }

        pricing = PricingService.calculate_base_booking_amount(vehicle_type, requested_hours=duration_hours)
        base_amount = pricing['total_amount']

        booking_code = cls.generate_booking_code()
        qr_token = f"SMARTPARK:{booking_code}:{vehicle_number}"

        now = datetime.utcnow()
        expected_start = now
        expected_end = now + timedelta(hours=duration_hours)
        expires_at = now + timedelta(minutes=hold_minutes)

        booking = Booking(
            booking_code=booking_code,
            user_id=user_id,
            vehicle_number=vehicle_number,
            vehicle_type=vehicle_type,
            slot_id=slot.id,
            customer_name=customer_name.strip(),
            customer_phone=customer_phone.strip(),
            customer_email=customer_email.strip(),
            expected_start_time=expected_start,
            expected_end_time=expected_end,
            base_hours=duration_hours,
            base_amount=Decimal(str(base_amount)),
            status='PENDING_PAYMENT',
            qr_token=qr_token,
            expires_at=expires_at,
            created_at=now
        )
        db.session.add(booking)
        db.session.flush()  # obtain booking.id

        # Update slot status to RESERVED with current booking reference
        slot.status = 'RESERVED'
        slot.current_booking_id = booking.id

        db.session.commit()

        return {
            'success': True,
            'booking_id': booking.id,
            'booking_code': booking.booking_code,
            'slot_number': slot.slot_number,
            'floor_zone': slot.floor_zone,
            'amount_to_pay': base_amount,
            'expires_at': expires_at.isoformat(),
            'hold_minutes': hold_minutes
        }

    @classmethod
    def confirm_booking_payment(
        cls,
        booking_id: int,
        payment_method: str = 'UPI'
    ) -> dict:
        """
        Validates payment and transitions booking to CONFIRMED.
        """
        booking = Booking.query.get(booking_id)
        if not booking:
            return {'success': False, 'message': 'Booking not found'}

        if booking.status == 'CONFIRMED':
            return {'success': True, 'booking': booking, 'message': 'Already confirmed'}

        if booking.status in ('EXPIRED', 'CANCELLED'):
            return {'success': False, 'message': f'Cannot pay for {booking.status.lower()} booking'}

        # Execute payment
        pay_res = PaymentService.process_payment(
            booking_id=booking.id,
            amount=float(booking.base_amount),
            payment_method=payment_method,
            payment_type='PREPAID'
        )

        if pay_res['success']:
            booking.status = 'CONFIRMED'
            db.session.commit()

            # Trigger notification
            NotificationService.notify_booking_confirmed(booking)

            return {
                'success': True,
                'booking': booking,
                'transaction_ref': pay_res['transaction_ref'],
                'message': 'Payment successful and slot reservation confirmed'
            }
        else:
            return {'success': False, 'message': 'Payment processing failed'}
