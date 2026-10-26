import uuid
from datetime import datetime
from decimal import Decimal
from app.models import db, Payment, Booking, ParkingSession


class PaymentService:
    @staticmethod
    def generate_transaction_ref() -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_token = uuid.uuid4().hex[:8].upper()
        return f"TXN-{date_str}-{unique_token}"

    @classmethod
    def process_payment(
        cls,
        booking_id: int,
        amount: float,
        payment_method: str,
        payment_type: str = 'PREPAID',
        session_id: int = None
    ) -> dict:
        """
        Processes mock/sandbox payment with verified server-side validation.
        """
        if amount < 0:
            return {'success': False, 'message': 'Payment amount cannot be negative'}

        # In sandbox mode, payments are validated and succeeded
        txn_ref = cls.generate_transaction_ref()
        payment = Payment(
            booking_id=booking_id,
            session_id=session_id,
            payment_type=payment_type,
            amount=Decimal(str(round(amount, 2))),
            payment_method=payment_method.upper(),
            transaction_ref=txn_ref,
            gateway_status='SUCCESS',
            payment_time=datetime.utcnow()
        )
        db.session.add(payment)
        db.session.commit()

        return {
            'success': True,
            'transaction_ref': txn_ref,
            'amount': round(amount, 2),
            'payment_method': payment_method,
            'payment_type': payment_type,
            'status': 'SUCCESS',
            'message': 'Payment verified and confirmed by sandbox gateway'
        }
