from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    retailer_id: Mapped[int] = mapped_column(ForeignKey("retailers.id"), index=True)
    deal_type: Mapped[str] = mapped_column(String(50))  # price_drop, price_error, clearance, coupon, lightning, delivery_glitch
    deal_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    regular_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    deal_score: Mapped[int] = mapped_column(default=0)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    is_historical_low: Mapped[bool] = mapped_column(default=False)
    found_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    notified_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    product = relationship("Product", back_populates="deals")
    retailer = relationship("Retailer", back_populates="deals")
