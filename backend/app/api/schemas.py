from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


# --- Retailer ---
class RetailerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    base_url: str
    logo_url: Optional[str] = None
    scraper_type: str
    tier: int
    is_enabled: bool
    requires_api_key: bool
    rate_limit_ms: int
    scrape_interval_minutes: int
    last_scraped_at: Optional[datetime] = None
    success_rate: float
    total_deals_found: int


class RetailerUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    scrape_interval_minutes: Optional[int] = None
    rate_limit_ms: Optional[int] = None


# --- Product ---
class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    retailer_id: int
    external_id: str
    name: str
    url: str
    image_url: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    current_price: Decimal
    original_price: Optional[Decimal] = None
    coupon_code: Optional[str] = None
    coupon_discount: Optional[Decimal] = None
    true_final_price: Optional[Decimal] = None
    in_stock: bool


class PriceHistoryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    price: Decimal
    original_price: Optional[Decimal] = None
    coupon_adjusted_price: Optional[Decimal] = None
    in_stock: bool
    recorded_at: datetime


class PriceHistoryResponse(BaseModel):
    product_id: int
    product_name: str
    history: list[PriceHistoryPoint]
    historical_low: Optional[Decimal] = None
    current_price: Decimal


# --- Deal ---
class DealResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    retailer_id: int
    deal_type: str
    deal_price: Decimal
    regular_price: Decimal
    discount_percent: Decimal
    deal_score: int
    coupon_code: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool
    is_historical_low: bool
    found_at: datetime
    last_seen_at: datetime
    expires_at: Optional[datetime] = None
    # Joined fields
    product_name: Optional[str] = None
    product_url: Optional[str] = None
    product_image: Optional[str] = None
    retailer_name: Optional[str] = None
    retailer_slug: Optional[str] = None


class DealListResponse(BaseModel):
    deals: list[DealResponse]
    total: int
    offset: int
    limit: int


class DealStatsResponse(BaseModel):
    total_active_deals: int
    avg_discount: float
    best_deal_score: int
    best_deal_title: Optional[str] = None
    deals_found_today: int
    retailers_monitored: int
    price_errors_found: int


# --- API Key ---
class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    service_name: str
    service_slug: str
    category: str
    masked_key: str
    is_valid: Optional[bool] = None
    last_tested_at: Optional[datetime] = None
    test_status: Optional[str] = None
    notes: Optional[str] = None


class ApiKeyCreate(BaseModel):
    service_name: str
    service_slug: str
    category: str
    key_value: str
    notes: Optional[str] = None


class ApiDirectoryEntry(BaseModel):
    service_name: str
    service_slug: str
    category: str
    description: str
    what_it_unlocks: str
    pricing_info: str
    signup_url: str
    is_free_tier: bool
    is_configured: bool = False


# --- Coupon ---
class CouponResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    retailer_id: int
    code: str
    description: Optional[str] = None
    discount_type: str
    discount_value: Decimal
    min_purchase: Optional[Decimal] = None
    is_verified: bool
    last_tested_at: Optional[datetime] = None
    success_rate: float
    times_used: int
    expires_at: Optional[datetime] = None


class CouponCreate(BaseModel):
    retailer_id: int
    code: str
    description: Optional[str] = None
    discount_type: str = "percent"
    discount_value: Decimal = Decimal("0")


# --- Scrape Job ---
class ScrapeJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    retailer_id: int
    status: str
    items_found: int
    deals_found: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    retailer_name: Optional[str] = None
