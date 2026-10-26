import logging
from datetime import datetime
from app.models import db, Notification

logger = logging.getLogger('SmartParkingNotifications')


class NotificationService:
    @staticmethod
    def dispatch(
        title: str,
        message: str,
        notification_type: str = 'INFO',
        user_id: int = None,
        booking_id: int = None,
        channel: str = 'IN_APP'
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            booking_id=booking_id,
            title=title,
            message=message,
            notification_type=notification_type,
            channel=channel,
            is_read=False,
            sent_at=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

        # Log simulated SMS / Email in console
        logger.info(f"[{channel.upper()} ALERT] To User {user_id or 'Guest'} (Booking {booking_id}): {title} - {message}")
        return notif

    @classmethod
    def notify_booking_confirmed(cls, booking):
        return cls.dispatch(
            title="Booking Confirmed! 🚗",
            message=f"Slot {booking.slot.slot_number} reserved for {booking.vehicle_number}. Pass Code: {booking.booking_code}",
            notification_type="SUCCESS",
            user_id=booking.user_id,
            booking_id=booking.id
        )

    @classmethod
    def notify_entry_authorized(cls, session):
        return cls.dispatch(
            title="Vehicle Entry Authorized 🟢",
            message=f"Vehicle {session.vehicle_number} entered parking at {session.entry_time.strftime('%I:%M %p')}. Slot: {session.slot.slot_number}.",
            notification_type="INFO",
            booking_id=session.booking_id
        )

    @classmethod
    def notify_30min_warning(cls, session):
        return cls.dispatch(
            title="30-Minute Expiry Warning ⏳",
            message=f"Vehicle {session.vehicle_number}: Only 30 minutes remaining in your prepaid base window. Please return to exit or extend your stay.",
            notification_type="WARNING",
            booking_id=session.booking_id
        )

    @classmethod
    def notify_overtime_started(cls, session, extra_rate):
        return cls.dispatch(
            title="Base Window Expired - Overtime Active ⚠️",
            message=f"Vehicle {session.vehicle_number}: Base 4-hour window has expired. Additional charges of ₹{extra_rate:.2f}/hour have started.",
            notification_type="ALERT",
            booking_id=session.booking_id
        )

    @classmethod
    def notify_exit_completed(cls, session):
        return cls.dispatch(
            title="Exit Successful - Have a Safe Trip! 👋",
            message=f"Vehicle {session.vehicle_number} exited at {session.exit_time.strftime('%I:%M %p')}. Total stay: {session.total_duration_minutes} minutes.",
            notification_type="SUCCESS",
            booking_id=session.booking_id
        )
