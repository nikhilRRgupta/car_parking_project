from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.models import ParkingSlot, Booking, ParkingSession, Notification
from app.services.booking_service import BookingService
from app.services.pricing_service import PricingService

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    BookingService.cleanup_expired_reservations()

    slots = ParkingSlot.query.order_by(ParkingSlot.floor_zone, ParkingSlot.slot_number).all()
    total_slots = len(slots)
    available_slots = sum(1 for s in slots if s.status == 'AVAILABLE')
    occupied_slots = sum(1 for s in slots if s.status == 'OCCUPIED')
    reserved_slots = sum(1 for s in slots if s.status == 'RESERVED')
    maintenance_slots = sum(1 for s in slots if s.status == 'MAINTENANCE')

    # Distinct zones for tabs/filtering
    zones = sorted(list(set(s.floor_zone for s in slots)))

    # Fetch default pricing rules for display
    rules = {
        '2-wheeler': PricingService.get_rule_for_vehicle('2-wheeler'),
        '4-wheeler': PricingService.get_rule_for_vehicle('4-wheeler'),
        'ev': PricingService.get_rule_for_vehicle('ev')
    }

    is_full = (available_slots == 0)

    return render_template(
        'public/index.html',
        slots=slots,
        total_slots=total_slots,
        available_slots=available_slots,
        occupied_slots=occupied_slots,
        reserved_slots=reserved_slots,
        maintenance_slots=maintenance_slots,
        zones=zones,
        rules=rules,
        is_full=is_full
    )


@public_bp.route('/live-slots')
def live_slots():
    BookingService.cleanup_expired_reservations()
    slots = ParkingSlot.query.order_by(ParkingSlot.floor_zone, ParkingSlot.slot_number).all()
    total = len(slots)
    available = sum(1 for s in slots if s.status == 'AVAILABLE')
    occupied = sum(1 for s in slots if s.status == 'OCCUPIED')
    reserved = sum(1 for s in slots if s.status == 'RESERVED')
    zones = sorted(list(set(s.floor_zone for s in slots)))

    return render_template(
        'public/live_slots.html',
        slots=slots,
        total=total,
        available=available,
        occupied=occupied,
        reserved=reserved,
        zones=zones,
        is_full=(available == 0)
    )


@public_bp.route('/pass/<booking_code>')
def view_pass(booking_code):
    booking = Booking.query.filter_by(booking_code=booking_code).first_or_404()
    qr_data_uri = BookingService.generate_qr_base64(booking.qr_token)

    # Check for active session
    session = ParkingSession.query.filter_by(booking_id=booking.id).first()

    # Get notifications for this booking
    notifications = Notification.query.filter_by(booking_id=booking.id).order_by(Notification.sent_at.desc()).all()

    # Current pricing rule
    rule = PricingService.get_rule_for_vehicle(booking.vehicle_type)

    return render_template(
        'public/view_pass.html',
        booking=booking,
        session=session,
        qr_data_uri=qr_data_uri,
        notifications=notifications,
        rule=rule
    )


@public_bp.route('/find-pass', methods=['GET', 'POST'])
def find_pass():
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        booking = Booking.query.filter(
            (Booking.booking_code == query) |
            (Booking.vehicle_number == query.upper().replace(" ", ""))
        ).order_by(Booking.id.desc()).first()

        if booking:
            return redirect(url_for('public.view_pass', booking_code=booking.booking_code))
        else:
            flash(f"No booking found matching '{query}'. Please verify your Booking ID or Vehicle Plate.", 'warning')

    return render_template('public/find_pass.html')
