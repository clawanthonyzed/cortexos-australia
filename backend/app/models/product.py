"""Digital product model."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin, UUIDMixin


class ProductStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    OUT_OF_STOCK = "out_of_stock"


class ProductType:
    DIGITAL_DOWNLOAD = "digital_download"
    SUBSCRIPTION = "subscription"
    SERVICE = "service"
    COURSE = "course"
    TEMPLATE = "template"
    TOOL = "tool"


class Product(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    product_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ProductType.DIGITAL_DOWNLOAD
    )
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")

    # Pricing (AUD)
    price_aud: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    original_price_aud: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_free: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ProductStatus.DRAFT, index=True
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Listings — external platform IDs as JSON
    listings_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}", server_default="{}")

    # Assets — file paths / URLs as JSON
    assets_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")

    # Cover image URL
    cover_image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Sales metrics
    total_sales: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_revenue_aud: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    view_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # SEO
    seo_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_keywords: Mapped[str] = mapped_column(Text, nullable=False, default="[]", server_default="[]")

    def __repr__(self) -> str:
        return f"<Product {self.name} ({self.status}) A${self.price_aud}>"
