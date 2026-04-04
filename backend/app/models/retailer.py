from datetime import datetime
from typing import Optional

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Retailer(Base):
    __tablename__ = "retailers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    base_url: Mapped[str] = mapped_column(String(500))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    scraper_type: Mapped[str] = mapped_column(String(50))  # api, playwright, rss
    tier: Mapped[int] = mapped_column(default=1)  # 1, 2, or 3
    is_enabled: Mapped[bool] = mapped_column(default=True)
    requires_api_key: Mapped[bool] = mapped_column(default=False)
    api_key_service: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rate_limit_ms: Mapped[int] = mapped_column(default=1000)
    scrape_interval_minutes: Mapped[int] = mapped_column(default=60)
    last_scraped_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    success_rate: Mapped[float] = mapped_column(default=0.0)
    total_deals_found: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    products = relationship("Product", back_populates="retailer", lazy="dynamic")
    deals = relationship("Deal", back_populates="retailer", lazy="dynamic")
    scrape_jobs = relationship("ScrapeJob", back_populates="retailer", lazy="dynamic")
    coupons = relationship("Coupon", back_populates="retailer", lazy="dynamic")
