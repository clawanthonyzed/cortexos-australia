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
    TokenUsageSummary,
)

logger = structlog.get_logger(__name__)
router = APIRouter()

AUD_PER_USD = 1.55  # Approximate exchange rate


@router.get("/dashboard", response_model=FinanceDashboard, tags=["finance"])
async def finance_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.FINANCE_READ)),
    days: int = Query(default=30, ge=1, le=365),
) -> FinanceDashboard:
    """
    Financial dashboard — revenue, costs, profit, sales for the past N days.
    Revenue data comes from products; costs from cost_records.
    """
    period_end = date.today()
    period_start = period_end - timedelta(days=days)
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
        )
        .where(CostRecord.created_at >= start_dt)
        .group_by(CostRecord.provider, CostRecord.model)
    )
    token_usage = [
        TokenUsageSummary(
            provider=row.provider,
            model=row.model,
            total_tokens=int(row.total_tokens or 0),
            prompt_tokens=int(row.prompt_tokens or 0),
            completion_tokens=int(row.completion_tokens or 0),
            cost_usd=float(row.total_cost or 0),
            period=f"last_{days}_days",
        )
        for row in cost_rows
    ]
    total_cost_usd = sum(t.cost_usd for t in token_usage)
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
        revenue_by_platform=[],  # Populated via platform sync
        monthly_trend=[],  # Populated by monthly aggregation endpoint
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
