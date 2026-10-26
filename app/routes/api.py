from datetime import datetime
from flask import Blueprint, jsonify, request
from app.models import db, ParkingSlot, Booking, ParkingSession, Notification
from app.services.booking_service import BookingService
from app.services.pricing_service import PricingService
from app.services.gate_service import GateService

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


@api_bp.route('/slots/live-status')
def live_slots_status():
    """
    Real-time JSON endpoint for live polling the parking lot status.
    Auto-expires unpaid reservations during polling.
    """
    BookingService.cleanup_expired_reservations()

    slots = ParkingSlot.query.order_by(ParkingSlot.floor_zone, ParkingSlot.slot_number).all()
    total = len(slots)
    available = sum(1 for s in slots if s.status == 'AVAILABLE')
    occupied = sum(1 for s in slots if s.status == 'OCCUPIED')
    reserved = sum(1 for s in slots if s.status == 'RESERVED')
    maintenance = sum(1 for s in slots if s.status == 'MAINTENANCE')

    slots_data = [s.to_dict() for s in slots]

    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'total': total,
        'available': available,
        'occupied': occupied,
        'reserved': reserved,
        'maintenance': maintenance,
        'is_full': (available == 0),
        'slots': slots_data
    })


@api_bp.route('/session/timer/<booking_code>')
def session_timer(booking_code):
    """
    Calculates live parking duration, remaining prepaid time, and overtime billing.
    """
    booking = Booking.query.filter_by(booking_code=booking_code).first()
    if not booking:
        return jsonify({'error': 'Booking not found'}), 404

    session = ParkingSession.query.filter_by(booking_id=booking.id).first()
    rule = PricingService.get_rule_for_vehicle(booking.vehicle_type)

    if not session or session.status == 'COMPLETED':
        return jsonify({
            'status': session.status if session else booking.status,
            'is_active': False,
            'entry_time': session.entry_time.isoformat() if session else None,
            'exit_time': session.exit_time.isoformat() if session and session.exit_time else None,
            'total_duration_minutes': session.total_duration_minutes if session else 0,
            'total_amount': float(session.total_amount) if session else float(booking.base_amount)
        })

    # Active in-progress session
    now = datetime.utcnow()
    delta = now - session.entry_time
    elapsed_seconds = int(delta.total_seconds())
    elapsed_minutes = max(0, elapsed_seconds // 60)

    base_minutes = rule.base_hours * 60
    remaining_base_minutes = base_minutes - elapsed_minutes

    bill = PricingService.calculate_exit_bill(
        entry_time=session.entry_time,
        exit_time=now,
        vehicle_type=booking.vehicle_type,
        prepaid_amount=float(session.prepaid_amount)
    )

    # Notification / Warning flags
    is_30min_warning = (0 < remaining_base_minutes <= 30)
    is_overtime = (remaining_base_minutes <= 0)

    return jsonify({
        'is_active': True,
        'status': 'IN_PROGRESS',
        'entry_time': session.entry_time.isoformat(),
        'elapsed_seconds': elapsed_seconds,
        'elapsed_minutes': elapsed_minutes,
        'base_hours': rule.base_hours,
        'base_minutes': base_minutes,
        'remaining_base_minutes': max(0, remaining_base_minutes),
        'overstay_minutes': max(0, -remaining_base_minutes),
        'hourly_rate': float(rule.hourly_rate_after_base),
        'prepaid_amount': float(session.prepaid_amount),
        'extra_charge': bill['extra_charge'],
        'gross_amount': bill['gross_amount'],
        'balance_due': bill['balance_due'],
        'is_30min_warning': is_30min_warning,
        'is_overtime': is_overtime
    })


@api_bp.route('/gate/authorize-entry', methods=['POST'])
def api_authorize_entry():
    data = request.get_json() or {}
    identifier = data.get('identifier', '')
    plate = data.get('vehicle_plate', '')
    res = GateService.validate_and_authorize_entry(identifier, plate, operator_name='API Gate Terminal')
    return jsonify(res)


@api_bp.route('/gate/prepare-exit', methods=['POST'])
def api_prepare_exit():
    data = request.get_json() or {}
    identifier = data.get('identifier', '')
    res = GateService.prepare_exit_bill(identifier)
    return jsonify(res)


@api_bp.route('/gate/complete-exit', methods=['POST'])
def api_complete_exit():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    payment_method = data.get('payment_method', 'UPI')
    res = GateService.complete_exit(session_id, payment_method, operator_name='API Gate Terminal')
    return jsonify(res)


@api_bp.route('/hardware/barrier/status')
def barrier_hardware_status():
    """
    Webhook endpoint for real boom barrier microcontrollers (ESP32 / Raspberry Pi).
    """
    gate = request.args.get('gate', 'ENTRY')
    return jsonify({
        'status': 'ONLINE',
        'gate': gate,
        'mode': 'SANDBOX_SIMULATION',
        'ready_for_trigger': True,
        'timestamp': datetime.utcnow().isoformat()
    })


@api_bp.route('/hardware/barrier/ack', methods=['POST'])
def barrier_hardware_ack():
    data = request.get_json() or {}
    # Microcontroller acknowledging physical barrier opened/closed
    return jsonify({'status': 'ACK_RECEIVED', 'data': data})
