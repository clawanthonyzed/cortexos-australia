export interface RevenueDataPoint {
  date: string;
  revenue: number;
  costs: number;
  profit: number;
}

export interface TokenUsageSummary {
  provider: string;
  model: string;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  percent_of_total: number;
  request_count: number;
  period: string;
}

export interface VentureFinancials {
  venture: string;
  revenueThisMonth: number;
  revenueLastMonth: number;
  costsThisMonth: number;
  profitThisMonth: number;
  growthPercent: number;
  revenueYtd: number;
}

export interface MonthlySummary {
  month: string;
  revenue_aud: number;
  cost_usd: number;
  cost_aud: number;
  profit_aud: number;
  sales_count: number;
  tokens_used: number;
}

export interface CostForecast {
  month: string;
  actual: number | null;
  projected: number;
  lowerBound: number;
  upperBound: number;
}

export interface FinanceDashboard {
  period_start: string;
  period_end: string;
  total_revenue_aud: number;
  total_cost_usd: number;
  total_profit_aud: number;
  active_products: number;
  total_sales: number;
  avg_order_value_aud: number;
  token_usage: TokenUsageSummary[];
  revenue_by_platform: Array<{ platform: string; revenue_aud: number; sales_count: number; period: string }>;
  monthly_trend: MonthlySummary[];
  revenue_history: RevenueDataPoint[];
  model_costs: TokenUsageSummary[];
}

/** Legacy camelCase alias — kept for components not yet migrated */
export interface ModelCostBreakdown {
  model: string;
  provider: string;
  tokensUsed: number;
  costUsd: number;
  percentOfTotal: number;
  requestCount: number;
}

export function tokenUsageToModelCost(t: TokenUsageSummary): ModelCostBreakdown {
  return {
    model: t.model,
    provider: t.provider,
    tokensUsed: t.total_tokens,
    costUsd: t.cost_usd,
    percentOfTotal: t.percent_of_total,
    requestCount: t.request_count,
  };
}

export interface FinanceSummary {
  revenueThisMonthAud: number;
  revenueLastMonthAud: number;
  revenueGrowthPercent: number;
  costsThisMonthUsd: number;
  costsLastMonthUsd: number;
  costsGrowthPercent: number;
  profitThisMonthAud: number;
  tokenUsageTodayM: number;
  tokenUsageMonthM: number;
  monthlyTarget: number;
  targetProgressPercent: number;
}
