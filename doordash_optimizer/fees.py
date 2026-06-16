from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from doordash_optimizer.models import Restaurant


def round_cents(value: float | Decimal) -> int:
    """Round monetary cents with conventional half-up behavior."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def rate_amount_cents(rate: float, subtotal_cents: int) -> int:
    return round_cents(Decimal(str(rate)) * subtotal_cents)


def final_cost_cents(discounted_subtotal_cents: int, restaurant: Restaurant) -> int:
    service_fee = rate_amount_cents(restaurant.service_fee_rate, discounted_subtotal_cents)
    tax = rate_amount_cents(restaurant.tax_rate, discounted_subtotal_cents)
    tip = rate_amount_cents(restaurant.tip_rate, discounted_subtotal_cents)
    small_order_fee = (
        restaurant.small_order_fee_cents
        if discounted_subtotal_cents < restaurant.small_order_threshold_cents
        else 0
    )
    return (
        discounted_subtotal_cents
        + restaurant.delivery_fee_cents
        + service_fee
        + tax
        + tip
        + small_order_fee
    )
