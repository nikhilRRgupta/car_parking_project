from datetime import datetime, timedelta
from app.services.pricing_service import PricingService


def test_base_booking_pricing(app):
    with app.app_context():
        # 4 hours for 4-wheeler should be base rate (₹50)
        calc = PricingService.calculate_base_booking_amount('4-wheeler', requested_hours=4)
        assert calc['total_amount'] == 50.00
        assert calc['extra_hours'] == 0

        # 6 hours for 4-wheeler (4 hrs @ ₹50 + 2 extra hrs @ ₹20 = ₹90)
        calc_extra = PricingService.calculate_base_booking_amount('4-wheeler', requested_hours=6)
        assert calc_extra['total_amount'] == 90.00
        assert calc_extra['extra_hours'] == 2


def test_exit_bill_within_base_and_grace(app):
    with app.app_context():
        entry = datetime.utcnow()
        # Stay: 4 hours and 10 minutes (within 15-minute grace period)
        exit_time = entry + timedelta(hours=4, minutes=10)
        bill = PricingService.calculate_exit_bill(entry, exit_time, '4-wheeler', prepaid_amount=50.0)

        assert bill['extra_hours'] == 0
        assert bill['extra_charge'] == 0.0
        assert bill['balance_due'] == 0.0
        assert bill['is_overdue'] is False


def test_exit_bill_overstay(app):
    with app.app_context():
        entry = datetime.utcnow()
        # Stay: 5 hours and 20 minutes (exceeded 4 hours + 15 min grace)
        # Overstay = 80 minutes - 15 min grace = 65 billable min -> ceil(65/60) = 2 started hours
        # Extra charge = 2 * ₹20 = ₹40
        exit_time = entry + timedelta(hours=5, minutes=20)
        bill = PricingService.calculate_exit_bill(entry, exit_time, '4-wheeler', prepaid_amount=50.0)

        assert bill['extra_hours'] == 2
        assert bill['extra_charge'] == 40.0
        assert bill['gross_amount'] == 90.0
        assert bill['balance_due'] == 40.0
        assert bill['is_overdue'] is True
