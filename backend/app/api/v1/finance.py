"""Finance endpoints — revenue, costs, forecasting."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

import structlog
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.dependencies import get_db, paginate
from app.models.cost_record import CostRecord
from app.models.product import Product, ProductStatus
from app.models.user import User
from app.schemas.finance import (
    CostRecordRead,
    FinanceDashboard,
    MonthlySummary,
    RevenueDataPoint,
    TokenUsageSummary,
)

logger = structlog.get_logger(__name__)
router = APIRouter()

AUD_PER_USD = 1.55  # Approximate exchange rate


def _period_to_days(period: str | None) -> int:
    mapping = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    return mapping.get(period or "30d", 30)


@router.get("/dashboard", response_model=FinanceDashboard, tags=["finance"])
async def finance_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_READ)),
    period: str | None = Query(default="30d"),
    days: int | None = Query(default=None, ge=1, le=365),
) -> FinanceDashboard:
    """
    Financial dashboard — revenue, costs, profit, sales.
    Accepts ?period=7d|30d|90d|1y (frontend) or ?days=N (legacy).
    """
    n_days = days if days is not None else _period_to_days(period)
    period_label = period or f"{n_days}d"

    period_end = date.today()
    period_start = period_end - timedelta(days=n_days)
    start_dt = datetime(period_start.year, period_start.month, period_start.day, tzinfo=timezone.utc)

    # Token / cost usage by provider+model
    cost_rows = await db.execute(
        select(
            CostRecord.provider,
            CostRecord.model,
            func.sum(CostRecord.total_tokens).label("total_tokens"),
            func.sum(CostRecord.prompt_tokens).label("prompt_tokens"),
            func.sum(CostRecord.completion_tokens).label("completion_tokens"),
            func.sum(CostRecord.cost_usd).label("total_cost"),
            func.count(CostRecord.id).label("request_count"),
        )
        .where(CostRecord.created_at >= start_dt)
        .group_by(CostRecord.provider, CostRecord.model)
    )
    raw_usage = [
        {
            "provider": row.provider,
            "model": row.model,
            "total_tokens": int(row.total_tokens or 0),
            "prompt_tokens": int(row.prompt_tokens or 0),
            "completion_tokens": int(row.completion_tokens or 0),
            "cost_usd": float(row.total_cost or 0),
            "request_count": int(row.request_count or 0),
        }
        for row in cost_rows
    ]
    total_cost_usd = sum(r["cost_usd"] for r in raw_usage)
    grand_total = total_cost_usd or 1.0  # avoid division by zero

    token_usage = [
        TokenUsageSummary(
            **r,
            period=period_label,
            percent_of_total=round((r["cost_usd"] / grand_total) * 100, 2),
        )
        for r in raw_usage
    ]
    model_costs = sorted(token_usage, key=lambda t: t.cost_usd, reverse=True)

    total_cost_aud = total_cost_usd * AUD_PER_USD

    # Product revenue
    products_result = await db.execute(
        select(
            func.count(Product.id).label("count"),
            func.sum(Product.total_revenue_aud).label("revenue"),
            func.sum(Product.total_sales).label("sales"),
        )
        .where(Product.status == ProductStatus.PUBLISHED)
    )
    prod_row = products_result.one()
    total_revenue = float(prod_row.revenue or 0)
    total_sales = int(prod_row.sales or 0)
    active_products = int(prod_row.count or 0)

    avg_order = total_revenue / total_sales if total_sales > 0 else 0.0
    profit = total_revenue - total_cost_aud

    # Daily cost breakdown for revenue_history chart
    daily_rows = await db.execute(
        select(
            func.date_trunc("day", CostRecord.created_at).label("day"),
            func.sum(CostRecord.cost_usd).label("daily_cost"),
        )
        .where(CostRecord.created_at >= start_dt)
        .group_by(func.date_trunc("day", CostRecord.created_at))
        .order_by(func.date_trunc("day", CostRecord.created_at))
    )
    daily_costs: dict[str, float] = {
        row.day.date().isoformat(): float(row.daily_cost or 0)
        for row in daily_rows
    }

    # Spread total_revenue evenly across days for the chart
    daily_revenue = total_revenue / n_days if n_days > 0 else 0.0
    revenue_history: list[RevenueDataPoint] = []
    for i in range(n_days):
        day = period_start + timedelta(days=i)
        day_str = day.isoformat()
        cost = daily_costs.get(day_str, 0.0)
        rev = daily_revenue
        revenue_history.append(RevenueDataPoint(
            date=day_str,
            revenue=round(rev, 2),
            costs=round(cost * AUD_PER_USD, 2),
            profit=round(rev - cost * AUD_PER_USD, 2),
        ))

    return FinanceDashboard(
        period_start=period_start,
        period_end=period_end,
        total_revenue_aud=round(total_revenue, 2),
        total_cost_usd=round(total_cost_usd, 4),
        total_profit_aud=round(profit, 2),
        active_products=active_products,
        total_sales=total_sales,
        avg_order_value_aud=round(avg_order, 2),
        token_usage=token_usage,
        revenue_by_platform=[],
        monthly_trend=[],
        revenue_history=revenue_history,
        model_costs=model_costs,
    )


@router.get("/costs", response_model=dict[str, Any], tags=["finance"])
async def list_costs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_READ)),
    pagination: dict = Depends(paginate),
    provider: str | None = Query(None),
    days: int = Query(default=30, ge=1, le=365),
) -> dict[str, Any]:
    """List cost records with pagination."""
    start_dt = datetime.now(tz=timezone.utc) - timedelta(days=days)

    stmt = select(CostRecord).where(CostRecord.created_at >= start_dt)
    if provider:
        stmt = stmt.where(CostRecord.provider == provider)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset(pagination["offset"]).limit(pagination["limit"]).order_by(CostRecord.created_at.desc())
    result = await db.execute(stmt)
    records = result.scalars().all()

    return {
        "items": [CostRecordRead.model_validate(r) for r in records],
        "total": total,
        "page": pagination["page"],
        "page_size": pagination["page_size"],
    }


@router.get("/monthly", tags=["finance"])
async def monthly_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_READ)),
    months: int = Query(default=6, ge=1, le=24),
) -> dict[str, Any]:
    """Monthly cost breakdown for the past N months."""
    rows = await db.execute(
        select(
            func.to_char(CostRecord.created_at, "YYYY-MM").label("month"),
            func.sum(CostRecord.cost_usd).label("cost_usd"),
            func.sum(CostRecord.total_tokens).label("tokens"),
        )
        .where(
            CostRecord.created_at >= datetime.now(tz=timezone.utc) - timedelta(days=months * 31)
        )
        .group_by(func.to_char(CostRecord.created_at, "YYYY-MM"))
        .order_by(func.to_char(CostRecord.created_at, "YYYY-MM").desc())
        .limit(months)
    )

    summaries = [
        {
            "month": row.month,
            "cost_usd": float(row.cost_usd or 0),
            "cost_aud": round(float(row.cost_usd or 0) * AUD_PER_USD, 2),
            "tokens_used": int(row.tokens or 0),
        }
        for row in rows
    ]
    return {"months": summaries}


@router.get("/revenue", tags=["finance"])
async def revenue_breakdown(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_READ)),
    period: str | None = Query(default="30d"),
    venture: str | None = Query(None, description="Filter by venture slug"),
) -> dict[str, Any]:
    """
    Real revenue breakdown from RevenueRecord table (Gumroad/Etsy/LemonSqueezy).
    Returns totals by platform, by venture, and daily time series.
    """
    from app.models.revenue_record import RevenueRecord

    n_days = _period_to_days(period)
    start_dt = datetime.now(tz=timezone.utc) - timedelta(days=n_days)

    stmt = select(RevenueRecord).where(RevenueRecord.created_at >= start_dt)
    if venture:
        stmt = stmt.where(RevenueRecord.venture_slug == venture)

    result = await db.execute(stmt.order_by(RevenueRecord.created_at.desc()))
    records = result.scalars().all()

    total_aud = sum(r.amount_aud for r in records)

    # Group by source
    by_source: dict[str, float] = {}
    for r in records:
        by_source[r.source] = by_source.get(r.source, 0.0) + r.amount_aud

    # Group by venture
    by_venture: dict[str, float] = {}
    for r in records:
        key = r.venture_slug or "unattributed"
        by_venture[key] = by_venture.get(key, 0.0) + r.amount_aud

    # Daily time series
    from collections import defaultdict
    daily: dict[str, float] = defaultdict(float)
    for r in records:
        day = r.created_at.date().isoformat()
        daily[day] += r.amount_aud

    return {
        "period": period,
        "total_revenue_aud": round(total_aud, 2),
        "record_count": len(records),
        "by_source": {k: round(v, 2) for k, v in sorted(by_source.items(), key=lambda x: -x[1])},
        "by_venture": {k: round(v, 2) for k, v in sorted(by_venture.items(), key=lambda x: -x[1])},
        "daily": {k: round(v, 2) for k, v in sorted(daily.items())},
        "note": "Set GUMROAD_API_KEY env var to enable live Gumroad sync",
    }


@router.post("/revenue/sync", tags=["finance"])
async def trigger_revenue_sync(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_READ)),
) -> dict[str, Any]:
    """Manually trigger a Gumroad revenue sync (also runs every 15 min automatically)."""
    from app.integrations.gumroad import sync_gumroad_sales
    inserted = await sync_gumroad_sales(db, lookback_days=7)
    return {"inserted": inserted, "message": f"Synced {inserted} new revenue records from Gumroad"}


@router.get("/forecast", tags=["finance"])
async def revenue_forecast(
    current_user: User = Depends(require_permission(Permission.FINANCE_READ)),
    horizon_months: int = Query(default=3, ge=1, le=12),
) -> dict[str, Any]:
    """
    Simple linear revenue forecast based on product target.
    Replace with a real model when historical data accumulates.
    """
    from datetime import datetime
    target_monthly_aud = 50_000  # $50K/month goal by 2026-07-22
    current_monthly_aud = 2_500   # Placeholder starting point

    # Linear ramp
    monthly_increment = (target_monthly_aud - current_monthly_aud) / 12.0

    forecast = []
    for i in range(1, horizon_months + 1):
        predicted = current_monthly_aud + (monthly_increment * i)
        forecast.append({
            "month": (datetime.now(tz=timezone.utc).replace(day=1) +
                      timedelta(days=32 * i)).strftime("%Y-%m"),
            "predicted_revenue_aud": round(predicted, 2),
            "lower_bound": round(predicted * 0.8, 2),
            "upper_bound": round(predicted * 1.2, 2),
            "confidence": 0.65,
        })

    return {
        "horizon_months": horizon_months,
        "forecast": forecast,
        "model_used": "linear_interpolation",
        "note": "Replace with ML model when 6+ months of data available",
    }
