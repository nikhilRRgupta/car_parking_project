from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import func
from app.models import db, ParkingSlot, Booking, ParkingSession, Payment, PricingRule, BarrierAuditLog, User
from app.auth_utils import role_required, login_required
from app.services.gate_service import GateService
from app.services.booking_service import BookingService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@role_required(['admin', 'attendant'])
def dashboard():
    BookingService.cleanup_expired_reservations()

    # Slot Stats
    slots = ParkingSlot.query.all()
    total_slots = len(slots)
    available_slots = sum(1 for s in slots if s.status == 'AVAILABLE')
    occupied_slots = sum(1 for s in slots if s.status == 'OCCUPIED')
    reserved_slots = sum(1 for s in slots if s.status == 'RESERVED')
    maintenance_slots = sum(1 for s in slots if s.status == 'MAINTENANCE')
    occupancy_pct = round((occupied_slots / total_slots * 100), 1) if total_slots > 0 else 0

    # Revenue Stats
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.payment_time >= today_start,
        Payment.gateway_status == 'SUCCESS'
    ).scalar() or 0.0

    total_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.gateway_status == 'SUCCESS'
    ).scalar() or 0.0

    # Active Sessions
    active_sessions = ParkingSession.query.filter_by(status='IN_PROGRESS').count()

    # Today's Bookings
    today_bookings = Booking.query.filter(Booking.created_at >= today_start).count()

    # Recent Bookings & Audit
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(8).all()
    recent_audits = BarrierAuditLog.query.order_by(BarrierAuditLog.timestamp.desc()).limit(8).all()

    # Chart Data: Vehicle distribution
    vehicle_types_query = db.session.query(
        Booking.vehicle_type, func.count(Booking.id)
    ).group_by(Booking.vehicle_type).all()
    vehicle_data = {v[0]: v[1] for v in vehicle_types_query}

    return render_template(
        'admin/dashboard.html',
        total_slots=total_slots,
        available_slots=available_slots,
        occupied_slots=occupied_slots,
        reserved_slots=reserved_slots,
        maintenance_slots=maintenance_slots,
        occupancy_pct=occupancy_pct,
        today_revenue=float(today_revenue),
        total_revenue=float(total_revenue),
        active_sessions=active_sessions,
        today_bookings=today_bookings,
        recent_bookings=recent_bookings,
        recent_audits=recent_audits,
        vehicle_data=vehicle_data
    )


@admin_bp.route('/slots', methods=['GET', 'POST'])
@role_required(['admin'])
def slots_manager():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            slot_number = request.form.get('slot_number', '').strip().upper()
            floor_zone = request.form.get('floor_zone', '').strip()
            vehicle_type = request.form.get('vehicle_type', '4-wheeler')
            is_ev = 'is_ev' in request.form

            if ParkingSlot.query.filter_by(slot_number=slot_number).first():
                flash(f"Slot {slot_number} already exists!", 'danger')
            else:
                new_slot = ParkingSlot(
                    slot_number=slot_number,
                    floor_zone=floor_zone,
                    vehicle_type=vehicle_type,
                    is_ev=is_ev,
                    status='AVAILABLE'
                )
                db.session.add(new_slot)
                db.session.commit()
                flash(f"Slot {slot_number} successfully added.", 'success')

        elif action == 'toggle_maintenance':
            slot_id = request.form.get('slot_id', type=int)
            slot = ParkingSlot.query.get(slot_id)
            if slot:
                if slot.status == 'MAINTENANCE':
                    slot.status = 'AVAILABLE'
                    flash(f"Slot {slot.slot_number} restored to AVAILABLE.", 'success')
                elif slot.status == 'AVAILABLE':
                    slot.status = 'MAINTENANCE'
                    flash(f"Slot {slot.slot_number} marked under MAINTENANCE.", 'warning')
                else:
                    flash(f"Cannot put slot {slot.slot_number} in maintenance while it is {slot.status}.", 'danger')
                db.session.commit()

        return redirect(url_for('admin.slots_manager'))

    all_slots = ParkingSlot.query.order_by(ParkingSlot.floor_zone, ParkingSlot.slot_number).all()
    zones = sorted(list(set(s.floor_zone for s in all_slots)))

    return render_template('admin/slots.html', slots=all_slots, zones=zones)


@admin_bp.route('/pricing', methods=['GET', 'POST'])
@role_required(['admin'])
def pricing_manager():
    if request.method == 'POST':
        for v_type in ['2-wheeler', '4-wheeler', 'ev']:
            base_rate = request.form.get(f'base_rate_{v_type}')
            hourly_rate = request.form.get(f'hourly_rate_{v_type}')
            base_hours = request.form.get(f'base_hours_{v_type}', 4, type=int)
            grace = request.form.get(f'grace_{v_type}', 15, type=int)

            if base_rate and hourly_rate:
                rule = PricingRule.query.filter_by(vehicle_type=v_type).first()
                if not rule:
                    rule = PricingRule(vehicle_type=v_type)
                    db.session.add(rule)
                rule.base_hours = base_hours
                rule.base_rate = Decimal(base_rate)
                rule.hourly_rate_after_base = Decimal(hourly_rate)
                rule.grace_period_minutes = grace
                rule.is_active = True

        db.session.commit()
        flash('Pricing rules updated successfully.', 'success')
        return redirect(url_for('admin.pricing_manager'))

    rules = {r.vehicle_type: r for r in PricingRule.query.all()}
    return render_template('admin/pricing.html', rules=rules)


@admin_bp.route('/bookings')
@role_required(['admin', 'attendant'])
def bookings_manager():
    status_filter = request.args.get('status')
    search_query = request.args.get('q', '').strip()

    query = Booking.query
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    if search_query:
        query = query.filter(
            (Booking.booking_code.like(f"%{search_query}%")) |
            (Booking.vehicle_number.like(f"%{search_query}%")) |
            (Booking.customer_name.like(f"%{search_query}%"))
        )

    bookings = query.order_by(Booking.created_at.desc()).limit(100).all()
    return render_template('admin/bookings.html', bookings=bookings, current_status=status_filter, query=search_query)


@admin_bp.route('/sessions')
@role_required(['admin', 'attendant'])
def sessions_manager():
    active_sessions = ParkingSession.query.filter_by(status='IN_PROGRESS').order_by(ParkingSession.entry_time.desc()).all()
    completed_sessions = ParkingSession.query.filter_by(status='COMPLETED').order_by(ParkingSession.exit_time.desc()).limit(50).all()
    return render_template('admin/sessions.html', active_sessions=active_sessions, completed_sessions=completed_sessions)


@admin_bp.route('/audit-logs')
@role_required(['admin', 'attendant'])
def audit_logs():
    logs = BarrierAuditLog.query.order_by(BarrierAuditLog.timestamp.desc()).limit(150).all()
    return render_template('admin/audit_logs.html', logs=logs)


@admin_bp.route('/barrier/manual-override', methods=['POST'])
@role_required(['admin', 'attendant'])
def manual_override():
    gate_type = request.form.get('gate_type', 'ENTRY')
    vehicle_number = request.form.get('vehicle_number', 'OVERRIDE')
    reason = request.form.get('reason', 'Emergency Staff Override')
    operator = request.form.get('operator_name', 'Admin Staff')

    res = GateService.manual_barrier_override(
        gate_type=gate_type,
        vehicle_number=vehicle_number,
        reason=reason,
        operator_name=operator
    )
    flash(res['message'], 'warning')
    return redirect(url_for('admin.dashboard'))
