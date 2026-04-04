from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("retailer_id", "external_id", name="uq_product_retailer_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    retailer_id: Mapped[int] = mapped_column(ForeignKey("retailers.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(300))
    name: Mapped[str] = mapped_column(String(500))
    url: Mapped[str] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    brand: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    model_number: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    upc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    current_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    original_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    coupon_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    coupon_discount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    true_final_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    in_stock: Mapped[bool] = mapped_column(default=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    last_checked_at: Mapped[datetime] = mapped_column(server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    retailer = relationship("Retailer", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product", lazy="dynamic")
    deals = relationship("Deal", back_populates="product", lazy="dynamic")
