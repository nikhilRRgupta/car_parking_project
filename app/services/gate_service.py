from datetime import datetime
from decimal import Decimal
from app.models import db, Booking, ParkingSlot, ParkingSession, BarrierAuditLog
from app.services.pricing_service import PricingService
from app.services.payment_service import PaymentService
from app.services.notification_service import NotificationService


class GateService:
    @classmethod
    def validate_and_authorize_entry(
        cls,
        identifier: str,
        vehicle_plate: str = None,
        operator_name: str = 'Auto Gate Controller'
    ) -> dict:
        """
        Validates booking, vehicle match, and payment status before raising entry barrier.
        """
        clean_id = identifier.strip() if identifier else ""
        clean_plate = vehicle_plate.strip().upper().replace(" ", "") if vehicle_plate else ""

        # Search by booking_code, qr_token, or vehicle_number
        booking = Booking.query.filter(
            (Booking.booking_code == clean_id) |
            (Booking.qr_token == clean_id) |
            (Booking.vehicle_number == clean_plate)
        ).order_by(Booking.id.desc()).first()

        if not booking:
            cls.log_barrier_event(
                gate_type='ENTRY',
                vehicle_number=clean_plate or 'UNKNOWN',
                booking_code=clean_id,
                action='DENY',
                reason='No matching reservation found for credentials',
                operator_name=operator_name
            )
            return {'success': False, 'message': 'No booking found for this code or vehicle number.'}

        # Check vehicle number if provided
        if clean_plate and booking.vehicle_number.replace(" ", "") != clean_plate:
            cls.log_barrier_event(
                gate_type='ENTRY',
                vehicle_number=clean_plate,
                booking_code=booking.booking_code,
                action='DENY',
                reason=f"Vehicle mismatch (Expected: {booking.vehicle_number}, Scanned: {clean_plate})",
                operator_name=operator_name
            )
            return {
                'success': False,
                'message': f"Vehicle plate mismatch! Booking is for {booking.vehicle_number}, detected {clean_plate}."
            }

        # Check booking status
        if booking.status == 'PENDING_PAYMENT':
            cls.log_barrier_event(
                gate_type='ENTRY',
                vehicle_number=booking.vehicle_number,
                booking_code=booking.booking_code,
                action='DENY',
                reason='Reservation has not been paid yet',
                operator_name=operator_name
            )
            return {'success': False, 'message': 'Payment pending! Please complete online payment before entry.'}

        if booking.status == 'ACTIVE':
            return {
                'success': False,
                'message': f"Vehicle {booking.vehicle_number} has already entered and has an active parking session."
            }

        if booking.status in ('COMPLETED', 'CANCELLED', 'EXPIRED'):
            cls.log_barrier_event(
                gate_type='ENTRY',
                vehicle_number=booking.vehicle_number,
                booking_code=booking.booking_code,
                action='DENY',
                reason=f"Booking is in {booking.status} state",
                operator_name=operator_name
            )
            return {'success': False, 'message': f"Cannot authorize entry. Booking is {booking.status.lower()}."}

        # Booking is CONFIRMED -> Authorize Entry!
        now = datetime.utcnow()
        session = ParkingSession(
            booking_id=booking.id,
            slot_id=booking.slot_id,
            vehicle_number=booking.vehicle_number,
            entry_time=now,
            prepaid_amount=booking.base_amount,
            extra_amount=Decimal('0.00'),
            total_amount=booking.base_amount,
            status='IN_PROGRESS'
        )
        db.session.add(session)

        # Transition statuses
        booking.status = 'ACTIVE'
        slot = ParkingSlot.query.get(booking.slot_id)
        if slot:
            slot.status = 'OCCUPIED'

        db.session.commit()

        # Audit Log
        cls.log_barrier_event(
            gate_type='ENTRY',
            vehicle_number=booking.vehicle_number,
            booking_code=booking.booking_code,
            action='OPEN',
            reason=f"Valid booking {booking.booking_code} and verified prepaid payment (₹{float(booking.base_amount):.2f})",
            operator_name=operator_name
        )

        # Notify
        NotificationService.notify_entry_authorized(session)

        return {
            'success': True,
            'message': f"Entry authorized for {booking.vehicle_number}! Slot {slot.slot_number if slot else ''} ({slot.floor_zone if slot else ''}).",
            'barrier_action': 'OPEN',
            'session_id': session.id,
            'booking_code': booking.booking_code,
            'slot_number': slot.slot_number if slot else 'N/A',
            'floor_zone': slot.floor_zone if slot else 'N/A',
            'entry_time': now.strftime('%I:%M %p')
        }

    @classmethod
    def prepare_exit_bill(cls, identifier: str) -> dict:
        """
        Looks up active session and calculates accurate real-time exit bill.
        """
        clean = identifier.strip().upper().replace(" ", "")

        session = ParkingSession.query.join(Booking).filter(
            ParkingSession.status == 'IN_PROGRESS',
            (ParkingSession.vehicle_number == clean) |
            (Booking.booking_code == identifier.strip()) |
            (Booking.qr_token == identifier.strip())
        ).order_by(ParkingSession.id.desc()).first()

        if not session:
            return {'success': False, 'message': 'No active in-progress parking session found for this vehicle/code.'}

        now = datetime.utcnow()
        vehicle_type = session.booking.vehicle_type
        prepaid = float(session.prepaid_amount)

        bill = PricingService.calculate_exit_bill(
            entry_time=session.entry_time,
            exit_time=now,
            vehicle_type=vehicle_type,
            prepaid_amount=prepaid
        )

        return {
            'success': True,
            'session_id': session.id,
            'booking_code': session.booking.booking_code,
            'vehicle_number': session.vehicle_number,
            'slot_number': session.slot.slot_number if session.slot else 'N/A',
            'entry_time': session.entry_time.strftime('%Y-%m-%d %I:%M %p'),
            'bill': bill
        }

    @classmethod
    def complete_exit(
        cls,
        session_id: int,
        payment_method: str = 'UPI',
        operator_name: str = 'Auto Gate Controller'
    ) -> dict:
        """
        Verifies bill settlement, processes overstay payment if applicable, opens barrier, releases slot.
        """
        session = ParkingSession.query.get(session_id)
        if not session or session.status != 'IN_PROGRESS':
            return {'success': False, 'message': 'Session is not active or already completed.'}

        now = datetime.utcnow()
        bill = PricingService.calculate_exit_bill(
            entry_time=session.entry_time,
            exit_time=now,
            vehicle_type=session.booking.vehicle_type,
            prepaid_amount=float(session.prepaid_amount)
        )

        balance_due = bill['balance_due']

        # If overstay payment needed, process and verify it on server
        if balance_due > 0:
            pay_res = PaymentService.process_payment(
                booking_id=session.booking_id,
                amount=balance_due,
                payment_method=payment_method,
                payment_type='EXIT_OVERSTAY',
                session_id=session.id
            )
            if not pay_res['success']:
                cls.log_barrier_event(
                    gate_type='EXIT',
                    vehicle_number=session.vehicle_number,
                    booking_code=session.booking.booking_code,
                    action='DENY',
                    reason=f"Failed payment for overtime charges: ₹{balance_due:.2f}",
                    operator_name=operator_name
                )
                return {'success': False, 'message': 'Payment for overstay failed. Exit denied.'}

        # Update session details
        session.exit_time = now
        session.total_duration_minutes = bill['total_minutes']
        session.extra_amount = Decimal(str(bill['extra_charge']))
        session.total_amount = Decimal(str(bill['gross_amount']))
        session.status = 'COMPLETED'

        # Update booking
        session.booking.status = 'COMPLETED'

        # Release slot genuinely
        slot = ParkingSlot.query.get(session.slot_id)
        if slot:
            slot.status = 'AVAILABLE'
            slot.current_booking_id = None

        db.session.commit()

        # Audit Log
        cls.log_barrier_event(
            gate_type='EXIT',
            vehicle_number=session.vehicle_number,
            booking_code=session.booking.booking_code,
            action='OPEN',
            reason=f"Authorized Exit: Total Stay {bill['formatted_duration']}, Final Bill ₹{bill['gross_amount']:.2f} (Paid in full)",
            operator_name=operator_name
        )

        # Notify
        NotificationService.notify_exit_completed(session)

        return {
            'success': True,
            'message': f"Exit authorized for {session.vehicle_number}. Slot {slot.slot_number if slot else ''} is now released.",
            'barrier_action': 'OPEN',
            'session_id': session.id,
            'vehicle_number': session.vehicle_number,
            'formatted_duration': bill['formatted_duration'],
            'total_amount': bill['gross_amount'],
            'extra_paid': balance_due
        }

    @classmethod
    def manual_barrier_override(
        gate_type: str,
        vehicle_number: str,
        reason: str,
        operator_name: str
    ) -> dict:
        clean_plate = vehicle_number.strip().upper().replace(" ", "") if vehicle_number else "MANUAL"
        GateService.log_barrier_event(
            gate_type=gate_type.upper(),
            vehicle_number=clean_plate,
            booking_code=None,
            action='MANUAL_OVERRIDE',
            reason=f"MANUAL OVERRIDE: {reason}",
            operator_name=operator_name
        )
        return {
            'success': True,
            'message': f"Manual override logged and barrier opened for {clean_plate} at {gate_type} gate.",
            'barrier_action': 'OPEN'
        }

    @staticmethod
    def log_barrier_event(
        gate_type: str,
        vehicle_number: str,
        booking_code: str,
        action: str,
        reason: str,
        operator_name: str
    ):
        log = BarrierAuditLog(
            gate_type=gate_type,
            vehicle_number=vehicle_number,
            booking_code=booking_code,
            action=action,
            reason=reason,
            operator_name=operator_name,
            timestamp=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
