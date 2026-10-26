import math
from datetime import datetime
from decimal import Decimal
from app.models import db, PricingRule


class PricingService:
    @staticmethod
    def get_rule_for_vehicle(vehicle_type: str) -> PricingRule:
        rule = PricingRule.query.filter_by(vehicle_type=vehicle_type, is_active=True).first()
        if not rule:
            # Fallback default rules if not initialized
            defaults = {
                '2-wheeler': {'base_hours': 4, 'base_rate': 20.0, 'hourly_rate': 10.0, 'grace': 15},
                '4-wheeler': {'base_hours': 4, 'base_rate': 50.0, 'hourly_rate': 20.0, 'grace': 15},
                'ev': {'base_hours': 4, 'base_rate': 40.0, 'hourly_rate': 15.0, 'grace': 15}
            }
            conf = defaults.get(vehicle_type, defaults['4-wheeler'])
            rule = PricingRule(
                vehicle_type=vehicle_type,
                base_hours=conf['base_hours'],
                base_rate=Decimal(str(conf['base_rate'])),
                hourly_rate_after_base=Decimal(str(conf['hourly_rate'])),
                grace_period_minutes=conf['grace'],
                is_active=True
            )
            db.session.add(rule)
            db.session.commit()
        return rule

    @classmethod
    def calculate_base_booking_amount(cls, vehicle_type: str, requested_hours: int = 4) -> dict:
        rule = cls.get_rule_for_vehicle(vehicle_type)
        base_rate = float(rule.base_rate)
        hourly_rate = float(rule.hourly_rate_after_base)

        if requested_hours <= rule.base_hours:
            amount = base_rate
            extra_hours = 0
        else:
            extra_hours = requested_hours - rule.base_hours
            amount = base_rate + (extra_hours * hourly_rate)

        return {
            'vehicle_type': vehicle_type,
            'base_hours': rule.base_hours,
            'requested_hours': requested_hours,
            'base_rate': base_rate,
            'hourly_rate': hourly_rate,
            'extra_hours': extra_hours,
            'total_amount': round(amount, 2)
        }

    @classmethod
    def calculate_exit_bill(
        cls,
        entry_time: datetime,
        exit_time: datetime,
        vehicle_type: str,
        prepaid_amount: float
    ) -> dict:
        """
        Accurately calculates final bill on exit:
        - Base duration (e.g. 4 hrs) covered by prepaid amount.
        - Additional started hours billed at hourly_rate_after_base.
        - Grace period applied before charging the next hour.
        - Returns net balance due (gross_amount - prepaid_amount).
        """
        rule = cls.get_rule_for_vehicle(vehicle_type)
        delta = exit_time - entry_time
        total_minutes = max(0, int(delta.total_seconds() // 60))

        base_duration_minutes = rule.base_hours * 60
        grace = rule.grace_period_minutes
        hourly_rate = float(rule.hourly_rate_after_base)
        base_rate = float(rule.base_rate)

        if total_minutes <= (base_duration_minutes + grace):
            # Exited within base window + grace
            extra_hours = 0
            extra_charge = 0.0
            gross_amount = max(base_rate, prepaid_amount)
        else:
            # Overstay beyond base duration
            overstay_minutes = total_minutes - base_duration_minutes
            # Subtract grace before billing additional started hours
            billable_overstay_minutes = max(0, overstay_minutes - grace)
            if billable_overstay_minutes == 0:
                extra_hours = 0
            else:
                extra_hours = math.ceil(billable_overstay_minutes / 60.0)

            extra_charge = round(extra_hours * hourly_rate, 2)
            gross_amount = round(prepaid_amount + extra_charge, 2)

        balance_due = max(0.0, round(gross_amount - prepaid_amount, 2))

        return {
            'vehicle_type': vehicle_type,
            'total_minutes': total_minutes,
            'formatted_duration': f"{total_minutes // 60}h {total_minutes % 60}m",
            'base_hours': rule.base_hours,
            'base_rate': base_rate,
            'hourly_rate': hourly_rate,
            'grace_period_minutes': grace,
            'extra_hours': extra_hours,
            'extra_charge': extra_charge,
            'gross_amount': gross_amount,
            'prepaid_amount': round(prepaid_amount, 2),
            'balance_due': balance_due,
            'is_overdue': balance_due > 0
        }
