from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Coupon(Base):
    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    retailer_id: Mapped[int] = mapped_column(ForeignKey("retailers.id"), index=True)
    code: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discount_type: Mapped[str] = mapped_column(String(50))  # percent, fixed, free_shipping
    discount_value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    min_purchase: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    categories: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list
    is_verified: Mapped[bool] = mapped_column(default=False)
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    success_rate: Mapped[float] = mapped_column(default=0.0)
    times_used: Mapped[int] = mapped_column(default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    retailer = relationship("Retailer", back_populates="coupons")
