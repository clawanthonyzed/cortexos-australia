"""Pydantic schemas for Finance endpoints."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class RevenueByPlatform(BaseModel):
    platform: str
    revenue_aud: float
    sales_count: int
    period: str


class MonthlySummary(BaseModel):
    month: str  # YYYY-MM
    revenue_aud: float
    cost_usd: float
    cost_aud: float  # Converted for display
    profit_aud: float
    sales_count: int
    tokens_used: int


class TokenUsageSummary(BaseModel):
    provider: str
    model: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    period: str


class ForecastPoint(BaseModel):
    month: str
    predicted_revenue_aud: float
    lower_bound: float
    upper_bound: float
    confidence: float


class RevenueForecast(BaseModel):
    horizon_months: int
    forecast: list[ForecastPoint]
    model_used: str
    generated_at: datetime


class FinanceDashboard(BaseModel):
    period_start: date
    period_end: date
    total_revenue_aud: float
    total_cost_usd: float
    total_profit_aud: float
    active_products: int
    total_sales: int
    avg_order_value_aud: float
    token_usage: list[TokenUsageSummary]
    revenue_by_platform: list[RevenueByPlatform]
    monthly_trend: list[MonthlySummary]


class CostRecordRead(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID | None
    task_id: uuid.UUID | None
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float
    trace_id: str | None
    label: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
