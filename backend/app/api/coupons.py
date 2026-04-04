from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.coupon import Coupon
from app.api.schemas import CouponResponse, CouponCreate

router = APIRouter(tags=["coupons"])


@router.get("/coupons", response_model=list[CouponResponse])
async def list_coupons(
    retailer_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Coupon)
    if retailer_id:
        query = query.where(Coupon.retailer_id == retailer_id)
    query = query.order_by(Coupon.is_verified.desc(), Coupon.success_rate.desc())
    result = await db.execute(query)
    return [CouponResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/coupons", response_model=CouponResponse)
async def create_coupon(data: CouponCreate, db: AsyncSession = Depends(get_db)):
    coupon = Coupon(
        retailer_id=data.retailer_id,
        code=data.code,
        description=data.description,
        discount_type=data.discount_type,
        discount_value=data.discount_value,
    )
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return CouponResponse.model_validate(coupon)


@router.delete("/coupons/{coupon_id}")
async def delete_coupon(coupon_id: int, db: AsyncSession = Depends(get_db)):
    coupon = await db.get(Coupon, coupon_id)
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    await db.delete(coupon)
    await db.commit()
    return {"status": "deleted"}
