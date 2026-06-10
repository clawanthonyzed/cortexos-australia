"""Gumroad sales sync — fetches new sales and upserts to revenue_records.

API docs: https://app.gumroad.com/api
Auth: Bearer token (GUMROAD_ACCESS_TOKEN env var)

Sales endpoint: GET /v2/sales
  Returns sales in reverse chronological order, paginated by `page_key`.
  Each sale has: id, product_name, price (cents USD), paid_at, email, referrer.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone, timedelta

import httpx
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.integrations.fx_rates import get_usd_aud_rate
from app.models.revenue_record import RevenueRecord, RevenueSource

logger = structlog.get_logger(__name__)

GUMROAD_API_BASE = "https://api.gumroad.com/v2"

# Map Gumroad product slugs/names to venture slugs
# Extend as empire grows
_PRODUCT_VENTURE_MAP: dict[str, str] = {
    "bloom": "bloom-and-bub",
    "bub": "bloom-and-bub",
    "kdp": "kdp-colouring-books",
    "colouring": "kdp-colouring-books",
    "color": "kdp-colouring-books",
    "mapdrop": "mapdrop",
    "map": "mapdrop",
    "lo-fi": "lo-fi-engine",
    "lofi": "lo-fi-engine",
    "meal": "meal-plan-cart",
    "affiliate": "affiliate-empire",
    "scroll": "scroll-and-stone",
    "footnote": "the-footnote",
    "sage": "sage-ai",
    "handwritten": "handwritten-book",
    "weekly": "weekly-wonder",
}


def _infer_venture(product_name: str) -> str | None:
    lower = product_name.lower()
    for keyword, venture in _PRODUCT_VENTURE_MAP.items():
        if keyword in lower:
            return venture
    return None


def _hash_email(email: str | None) -> str | None:
    if not email:
        return None
    return hashlib.sha256(email.encode()).hexdigest()


async def sync_gumroad_sales(db: AsyncSession, lookback_days: int = 2) -> int:
    """
    Pull recent Gumroad sales and upsert to revenue_records.
    Returns count of new records inserted.
    """
    api_key = os.environ.get("GUMROAD_ACCESS_TOKEN", "")
    if not api_key:
        logger.warning("GUMROAD_ACCESS_TOKEN not set — skipping Gumroad sync")
        return 0

    fx_rate = await get_usd_aud_rate()
    after_dt = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
    inserted = 0
    page_key: str | None = None

    async with httpx.AsyncClient(
        base_url=GUMROAD_API_BASE,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=30.0,
    ) as client:
        while True:
            params: dict[str, str] = {"after": after_dt.strftime("%Y-%m-%d")}
            if page_key:
                params["page_key"] = page_key

            try:
                resp = await client.get("/sales", params=params)
                resp.raise_for_status()
                body = resp.json()
            except Exception as exc:
                logger.error("Gumroad API error", error=str(exc))
                break

            sales = body.get("sales", [])
            if not sales:
                break

            for sale in sales:
                external_id = sale.get("id", "")
                if not external_id:
                    continue

                # Check for duplicate
                existing = await db.execute(
                    select(RevenueRecord).where(
                        RevenueRecord.source == RevenueSource.GUMROAD,
                        RevenueRecord.external_id == external_id,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                amount_cents = int(sale.get("price", 0) or 0)
                amount_usd = amount_cents / 100.0
                amount_aud = round(amount_usd * fx_rate, 2)
                product_name = sale.get("product_name", "")

                record = RevenueRecord(
                    source=RevenueSource.GUMROAD,
                    external_id=external_id,
                    venture_slug=_infer_venture(product_name),
                    product_name=product_name,
                    amount_native=amount_usd,
                    currency_native="USD",
                    amount_aud=amount_aud,
                    fx_rate_usd_aud=fx_rate,
                    buyer_email_hash=_hash_email(sale.get("email")),
                    raw_json=json.dumps(sale),
                )
                db.add(record)
                inserted += 1

            await db.flush()

            # Pagination
            next_page = body.get("next_page_key")
            if not next_page or not sales:
                break
            page_key = next_page

    logger.info("Gumroad sync complete", inserted=inserted)
    return inserted
