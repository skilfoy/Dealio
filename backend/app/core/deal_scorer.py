from datetime import datetime, timezone


def calculate_deal_score(
    discount_percent: float,
    price_history_count: int,
    in_stock: bool,
    retailer_tier: int,
    deal_type: str,
    found_at: datetime,
    is_historical_low: bool = False,
) -> int:
    score = 0.0

    # Discount depth (0-30 points)
    if discount_percent >= 90:
        score += 30
    elif discount_percent >= 50:
        score += 15 + (discount_percent - 50) * (15 / 40)
    else:
        score += discount_percent * (15 / 50)

    # Price history confidence (0-20 points)
    if price_history_count >= 10:
        score += 20
    elif price_history_count >= 5:
        score += 15
    elif price_history_count >= 2:
        score += 10
    elif price_history_count >= 1:
        score += 5
    else:
        score += 3  # New product, some baseline

    # Stock urgency (0-15 points)
    if in_stock:
        score += 10
    # Out of stock gets 0

    # Source reliability (0-15 points)
    tier_scores = {1: 15, 2: 10, 3: 7}
    score += tier_scores.get(retailer_tier, 5)

    # Deal type bonus (0-10 points)
    type_scores = {
        "price_error": 10,
        "delivery_glitch": 10,
        "clearance": 7,
        "lightning": 6,
        "price_drop": 5,
        "coupon": 4,
    }
    score += type_scores.get(deal_type, 3)

    # Recency (0-10 points)
    now = datetime.now(timezone.utc)
    if found_at.tzinfo is None:
        found_at = found_at.replace(tzinfo=timezone.utc)
    age_hours = (now - found_at).total_seconds() / 3600
    if age_hours < 1:
        score += 10
    elif age_hours < 6:
        score += 7
    elif age_hours < 24:
        score += 5
    else:
        score += 2

    # Historical low bonus
    if is_historical_low:
        score += 5

    return max(0, min(100, round(score)))
