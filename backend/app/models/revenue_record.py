"""Revenue record — tracks real sales from Gumroad, Etsy, LemonSqueezy."""
from __future__ import annotations

import uuid

from sqlalchemy import Float, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin, UUIDMixin


class RevenueSource:
    GUMROAD = "gumroad"
    ETSY = "etsy"
    LEMON_SQUEEZY = "lemon_squeezy"
    MANUAL = "manual"


class RevenueRecord(Base, UUIDMixin, TimestampMixin):
    """
    One row per sale event from an external platform.
    `external_id` is platform-scoped and deduplicated on (source, external_id).
    """
    __tablename__ = "revenue_records"

    # Platform that generated this sale
    source: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    # Platform-native order/sale ID — used for deduplication
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Venture slug (e.g. 'bloom-and-bub', 'kdp-colouring-books')
    venture_slug: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Product identifier (platform slug/name)
    product_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Amount in native platform currency (USD for Gumroad/LemonSqueezy, AUD for Etsy AU)
    amount_native: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency_native: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # Canonical AUD amount (converted via daily FX rate)
    amount_aud: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # FX rate used for conversion
    fx_rate_usd_aud: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # Buyer email (hashed for privacy)
    buyer_email_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Raw platform payload stored as JSON for audit
    raw_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_revenue_source_external"),
        Index("ix_revenue_venture_slug_created", "venture_slug", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<RevenueRecord {self.source}:{self.external_id} A${self.amount_aud:.2f}>"
