export interface RevenueDataPoint {
  date: string;
  revenue: number;
  costs: number;
  profit: number;
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

export interface ModelCostBreakdown {
  model: string;
  provider: string;
  tokensUsed: number;
  costUsd: number;
  percentOfTotal: number;
  requestCount: number;
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

export interface CostForecast {
  month: string;
  actual: number | null;
  projected: number;
  lowerBound: number;
  upperBound: number;
}

export interface FinanceDashboard {
  summary: FinanceSummary;
  revenueHistory: RevenueDataPoint[];
  ventureBreakdown: VentureFinancials[];
  modelCosts: ModelCostBreakdown[];
  forecast: CostForecast[];
}
