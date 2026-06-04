"""Pydantic schemas for Product."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProductListingInfo(BaseModel):
    platform: str
    listing_id: str
    url: str | None = None
    status: str = "active"
    synced_at: datetime | None = None


class ProductAsset(BaseModel):
    name: str
    url: str
    file_type: str
    size_bytes: int | None = None


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    short_description: str | None = None
    product_type: str = Field(default="digital_download")
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    price_aud: float = Field(default=0.0, ge=0.0)
    original_price_aud: float | None = Field(None, ge=0.0)
    is_free: bool = False
    cover_image_url: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: list[str] = Field(default_factory=list)


class ProductCreate(ProductBase):
    listings: dict[str, ProductListingInfo] = Field(default_factory=dict)
    assets: list[ProductAsset] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    product_type: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    price_aud: float | None = Field(None, ge=0.0)
    original_price_aud: float | None = None
    is_free: bool | None = None
    status: str | None = None
    is_featured: bool | None = None
    cover_image_url: str | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_keywords: list[str] | None = None


class ProductRead(ProductBase):
    id: uuid.UUID
    status: str
    is_featured: bool
    listings: dict[str, Any] = Field(default_factory=dict)
    assets: list[Any] = Field(default_factory=list)
    total_sales: int
    total_revenue_aud: float
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductReadBrief(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    status: str
    price_aud: float
    total_sales: int
    total_revenue_aud: float

    model_config = {"from_attributes": True}
