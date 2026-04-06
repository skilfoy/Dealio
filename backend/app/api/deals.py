from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.deal import Deal
from app.models.product import Product
from app.models.retailer import Retailer
from app.api.schemas import DealResponse, DealListResponse, DealStatsResponse

router = APIRouter(tags=["deals"])


def _deal_to_response(deal: Deal, product: Product | None = None, retailer: Retailer | None = None) -> DealResponse:
    return DealResponse(
        id=deal.id,
        product_id=deal.product_id,
        retailer_id=deal.retailer_id,
        deal_type=deal.deal_type,
        deal_price=deal.deal_price,
        regular_price=deal.regular_price,
        discount_percent=deal.discount_percent,
        deal_score=deal.deal_score,
        coupon_code=deal.coupon_code,
        title=deal.title or (product.name if product else None),
        description=deal.description,
        source_url=deal.source_url or (product.url if product else None),
        image_url=deal.image_url or (product.image_url if product else None),
        is_active=deal.is_active,
        is_historical_low=deal.is_historical_low,
        found_at=deal.found_at,
        last_seen_at=deal.last_seen_at,
        expires_at=deal.expires_at,
        product_name=product.name if product else None,
        product_url=product.url if product else None,
        product_image=product.image_url if product else None,
        retailer_name=retailer.name if retailer else None,
        retailer_slug=retailer.slug if retailer else None,
    )


@router.get("/deals", response_model=DealListResponse)
async def list_deals(
    db: AsyncSession = Depends(get_db),
    retailer: Optional[str] = Query(None),
    deal_type: Optional[str] = Query(None),
    min_score: int = Query(0, ge=0, le=100),
    min_discount: int = Query(0, ge=0, le=100),
    max_price: Optional[float] = Query(None),
    min_price: Optional[float] = Query(None),
    in_stock: Optional[bool] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    sort: str = Query("score", regex="^(score|discount|newest|price)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    query = select(Deal, Product, Retailer).join(Product, Deal.product_id == Product.id).join(Retailer, Deal.retailer_id == Retailer.id)

    conditions = []
    if active_only:
        conditions.append(Deal.is_active == True)
    if retailer:
        conditions.append(Retailer.slug == retailer)
    if deal_type:
        conditions.append(Deal.deal_type == deal_type)
    if min_score > 0:
        conditions.append(Deal.deal_score >= min_score)
    if min_discount > 0:
        conditions.append(Deal.discount_percent >= min_discount)
    if max_price is not None:
        conditions.append(Deal.deal_price <= max_price)
    if min_price is not None:
        conditions.append(Deal.deal_price >= min_price)
    if in_stock is not None:
        conditions.append(Product.in_stock == in_stock)
    if category:
        conditions.append(Product.category == category)
    if search:
        conditions.append(Product.name.ilike(f"%{search}%"))

    if conditions:
        query = query.where(and_(*conditions))

    # Count
    count_query = select(func.count()).select_from(Deal)
    if conditions:
        count_query = count_query.join(Product, Deal.product_id == Product.id).join(Retailer, Deal.retailer_id == Retailer.id).where(and_(*conditions))
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    sort_map = {
        "score": desc(Deal.deal_score),
        "discount": desc(Deal.discount_percent),
        "newest": desc(Deal.found_at),
        "price": asc(Deal.deal_price),
    }
    query = query.order_by(sort_map.get(sort, desc(Deal.deal_score)))
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    rows = result.all()
    deals = [_deal_to_response(deal, product, ret) for deal, product, ret in rows]

    return DealListResponse(deals=deals, total=total, offset=offset, limit=limit)


@router.get("/deals/stats", response_model=DealStatsResponse)
async def deal_stats(db: AsyncSession = Depends(get_db)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    total = (await db.execute(select(func.count()).where(Deal.is_active == True))).scalar() or 0
    avg_disc = (await db.execute(select(func.avg(Deal.discount_percent)).where(Deal.is_active == True))).scalar() or 0
    best = (await db.execute(select(Deal).where(Deal.is_active == True).order_by(desc(Deal.deal_score)).limit(1))).scalars().first()
    today_count = (await db.execute(select(func.count()).where(and_(Deal.is_active == True, Deal.found_at >= today)))).scalar() or 0
    retailers_count = (await db.execute(select(func.count()).where(Retailer.is_enabled == True))).scalar() or 0
    errors_count = (await db.execute(select(func.count()).where(and_(Deal.is_active == True, Deal.deal_type == "price_error")))).scalar() or 0

    return DealStatsResponse(
        total_active_deals=total,
        avg_discount=round(float(avg_disc), 1),
        best_deal_score=best.deal_score if best else 0,
        best_deal_title=best.title if best else None,
        deals_found_today=today_count,
        retailers_monitored=retailers_count,
        price_errors_found=errors_count,
    )


@router.get("/deals/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Deal, Product, Retailer)
        .join(Product, Deal.product_id == Product.id)
        .join(Retailer, Deal.retailer_id == Retailer.id)
        .where(Deal.id == deal_id)
    )
    row = result.first()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Deal not found")
    deal, product, retailer = row
    return _deal_to_response(deal, product, retailer)
