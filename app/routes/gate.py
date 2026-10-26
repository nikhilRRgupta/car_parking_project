from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from app.models import db, ParkingSession, Booking, ParkingSlot, BarrierAuditLog
from app.services.gate_service import GateService

gate_bp = Blueprint('gate', __name__, url_prefix='/gate')


@gate_bp.route('/entry', methods=['GET', 'POST'])
def entry_station():
    result = None
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        vehicle_plate = request.form.get('vehicle_plate', '').strip()
        operator = session.get('user_name', 'Gate Station 1')

        result = GateService.validate_and_authorize_entry(
            identifier=identifier,
            vehicle_plate=vehicle_plate,
            operator_name=operator
        )

    recent_logs = BarrierAuditLog.query.filter_by(gate_type='ENTRY').order_by(BarrierAuditLog.timestamp.desc()).limit(5).all()

    return render_template(
        'gate/entry_terminal.html',
        result=result,
        recent_logs=recent_logs
    )


@gate_bp.route('/exit', methods=['GET', 'POST'])
def exit_station():
    lookup_result = None
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        lookup_result = GateService.prepare_exit_bill(identifier)

    recent_logs = BarrierAuditLog.query.filter_by(gate_type='EXIT').order_by(BarrierAuditLog.timestamp.desc()).limit(5).all()

    return render_template(
        'gate/exit_terminal.html',
        lookup=lookup_result,
        recent_logs=recent_logs
    )


@gate_bp.route('/exit/complete', methods=['POST'])
def exit_complete():
    session_id = request.form.get('session_id', type=int)
    payment_method = request.form.get('payment_method', 'UPI')
    operator = session.get('user_name', 'Exit Station 1')

    result = GateService.complete_exit(
        session_id=session_id,
        payment_method=payment_method,
        operator_name=operator
    )

    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')

    return redirect(url_for('gate.exit_station'))


@gate_bp.route('/barrier-simulator')
def barrier_simulator():
    """
    Interactive graphical barrier simulator showing both Entry & Exit boom barriers
    with live hardware LED indicators and audio effects.
    """
    active_sessions = ParkingSession.query.filter_by(status='IN_PROGRESS').order_by(ParkingSession.entry_time.desc()).all()
    recent_bookings = Booking.query.filter(Booking.status.in_(['CONFIRMED', 'ACTIVE'])).order_by(Booking.id.desc()).limit(10).all()

    return render_template(
        'gate/barrier_sim.html',
        active_sessions=active_sessions,
        recent_bookings=recent_bookings
    )
