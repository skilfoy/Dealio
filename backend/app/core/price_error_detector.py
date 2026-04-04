"""Detects price errors on EVERY price update, not just new products.

Heuristics:
- Price < $1 for items previously > $50
- 90%+ sudden price drop
- Price ending in unusual cents (0.09, 0.01) on items > $10 originally
- Delivery app items at fraction of known retail price
"""

from decimal import Decimal
from typing import Optional


def detect_price_error(
    new_price: Decimal,
    previous_price: Optional[Decimal],
    original_price: Optional[Decimal],
    avg_historical_price: Optional[Decimal],
    is_delivery_app: bool = False,
) -> tuple[bool, str]:
    """
    Returns (is_price_error, reason).
    Runs on every price update.
    """
    if new_price <= 0:
        return False, ""

    reference_price = previous_price or original_price or avg_historical_price

    # Heuristic 1: Price under $1 for items previously > $50
    if reference_price and reference_price > 50 and new_price < 1:
        return True, f"Price dropped to ${new_price} from ${reference_price} — likely pricing error"

    # Heuristic 2: 90%+ sudden drop
    if reference_price and reference_price > 0:
        drop_pct = float((reference_price - new_price) / reference_price * 100)
        if drop_pct >= 90:
            return True, f"{drop_pct:.0f}% price drop — possible pricing error"

    # Heuristic 3: Unusual cent endings on items that were > $10
    if reference_price and reference_price > 10:
        cents = int(new_price * 100) % 100
        if cents in (1, 9) and new_price < reference_price * Decimal("0.2"):
            return True, f"Unusual price ${new_price} (ends in .{cents:02d}) — possible glitch"

    # Heuristic 4: Delivery app glitch — item at fraction of retail
    if is_delivery_app and avg_historical_price and avg_historical_price > 5:
        if new_price < avg_historical_price * Decimal("0.1"):
            return True, f"Delivery app price ${new_price} vs retail ${avg_historical_price} — likely glitch"

    return False, ""


def classify_deal_type(
    discount_percent: float,
    is_price_error: bool,
    is_delivery_app: bool = False,
    has_coupon: bool = False,
    is_clearance: bool = False,
) -> str:
    if is_price_error and is_delivery_app:
        return "delivery_glitch"
    if is_price_error:
        return "price_error"
    if is_clearance:
        return "clearance"
    if has_coupon:
        return "coupon"
    if discount_percent >= 70:
        return "lightning"
    return "price_drop"
