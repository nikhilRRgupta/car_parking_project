from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, ParkingSlot, Booking
from app.services.booking_service import BookingService
from app.services.pricing_service import PricingService
from app.services.payment_service import PaymentService

booking_bp = Blueprint('booking', __name__, url_prefix='/booking')


@booking_bp.route('/book', methods=['GET', 'POST'])
def book_slot():
    BookingService.cleanup_expired_reservations()

    if request.method == 'POST':
        slot_id = request.form.get('slot_id', type=int)
        vehicle_number = request.form.get('vehicle_number', '').strip()
        vehicle_type = request.form.get('vehicle_type', '4-wheeler')
        customer_name = request.form.get('customer_name', '').strip()
        customer_phone = request.form.get('customer_phone', '').strip()
        customer_email = request.form.get('customer_email', '').strip()
        duration_hours = request.form.get('duration_hours', 4, type=int)

        if not (slot_id and vehicle_number and customer_name and customer_phone and customer_email):
            flash('Please complete all required fields.', 'danger')
            return redirect(url_for('booking.book_slot', vehicle_type=vehicle_type, slot_id=slot_id))

        user_id = session.get('user_id')

        # Concurrency-safe slot reservation
        res = BookingService.reserve_slot_concurrency_safe(
            slot_id=slot_id,
            vehicle_number=vehicle_number,
            vehicle_type=vehicle_type,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            user_id=user_id,
            duration_hours=duration_hours,
            hold_minutes=10
        )

        if res['success']:
            flash('Slot held for 10 minutes. Please complete payment to confirm your booking.', 'info')
            return redirect(url_for('booking.checkout', booking_id=res['booking_id']))
        else:
            flash(res['message'], 'danger')
            return redirect(url_for('booking.book_slot', vehicle_type=vehicle_type))

    # GET request
    preselected_type = request.args.get('vehicle_type', '4-wheeler')
    preselected_slot_id = request.args.get('slot_id', type=int)

    # Fetch available slots
    query = ParkingSlot.query.filter_by(status='AVAILABLE')
    if preselected_type == 'ev':
        query = query.filter_by(is_ev=True)
    elif preselected_type:
        query = query.filter_by(vehicle_type=preselected_type)

    available_slots = query.order_by(ParkingSlot.floor_zone, ParkingSlot.slot_number).all()

    rules = {
        '2-wheeler': PricingService.get_rule_for_vehicle('2-wheeler'),
        '4-wheeler': PricingService.get_rule_for_vehicle('4-wheeler'),
        'ev': PricingService.get_rule_for_vehicle('ev')
    }

    return render_template(
        'booking/book_slot.html',
        available_slots=available_slots,
        selected_type=preselected_type,
        selected_slot_id=preselected_slot_id,
        rules=rules
    )


@booking_bp.route('/checkout/<int:booking_id>')
def checkout(booking_id):
    BookingService.cleanup_expired_reservations()
    booking = Booking.query.get_or_404(booking_id)

    if booking.status == 'CONFIRMED':
        flash('This booking is already confirmed and paid.', 'success')
        return redirect(url_for('public.view_pass', booking_code=booking.booking_code))

    if booking.status in ('EXPIRED', 'CANCELLED'):
        flash('This reservation has expired or was cancelled. Please book again.', 'warning')
        return redirect(url_for('booking.book_slot'))

    # Calculate remaining hold time in seconds
    now = datetime.utcnow()
    seconds_remaining = max(0, int((booking.expires_at - now).total_seconds())) if booking.expires_at else 0

    return render_template(
        'booking/payment.html',
        booking=booking,
        seconds_remaining=seconds_remaining
    )


@booking_bp.route('/checkout/<int:booking_id>/pay', methods=['POST'])
def process_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    payment_method = request.form.get('payment_method', 'UPI')

    result = BookingService.confirm_booking_payment(
        booking_id=booking.id,
        payment_method=payment_method
    )

    if result['success']:
        flash('Payment verified successfully! Your digital parking pass is ready.', 'success')
        return redirect(url_for('public.view_pass', booking_code=booking.booking_code))
    else:
        flash(result['message'], 'danger')
        return redirect(url_for('booking.checkout', booking_id=booking.id))


@booking_bp.route('/cancel/<int:booking_id>', methods=['POST'])
def cancel_reservation(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.status == 'PENDING_PAYMENT':
        booking.status = 'CANCELLED'
        if booking.slot and booking.slot.status == 'RESERVED':
            booking.slot.status = 'AVAILABLE'
            booking.slot.current_booking_id = None
        db.session.commit()
        flash('Reservation was cancelled and slot released.', 'info')
    return redirect(url_for('public.index'))
