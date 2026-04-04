from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.product import Product
from app.models.price_history import PriceHistory
from app.api.schemas import ProductResponse, PriceHistoryResponse, PriceHistoryPoint

router = APIRouter(tags=["products"])


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.get("/products/{product_id}/price-history", response_model=PriceHistoryResponse)
async def get_price_history(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id, PriceHistory.recorded_at >= since)
        .order_by(asc(PriceHistory.recorded_at))
    )
    history = result.scalars().all()

    # Find historical low from ALL history
    low_result = await db.execute(
        select(func.min(PriceHistory.price)).where(PriceHistory.product_id == product_id)
    )
    historical_low = low_result.scalar()

    return PriceHistoryResponse(
        product_id=product.id,
        product_name=product.name,
        history=[PriceHistoryPoint.model_validate(h) for h in history],
        historical_low=historical_low,
        current_price=product.current_price,
    )
