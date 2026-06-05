"use client";

import { useState } from "react";
import {
  DollarSign, TrendingUp, TrendingDown, Cpu, Target, ArrowUpRight, ArrowDownRight
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { RevenueBreakdown } from "@/components/finance/revenue-breakdown";
import { CostBreakdown } from "@/components/finance/cost-breakdown";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useFinance } from "@/hooks/use-finance";
import { formatCurrency, formatPercent, formatTokens } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { tokenUsageToModelCost } from "@/types/finance";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const MONTHLY_TARGET = 50_000;

export default function FinancePage() {
  const [period, setPeriod] = useState<"7d" | "30d" | "90d" | "1y">("30d");
  const { data, isLoading } = useFinance({ period });

  const totalRevenue = data?.total_revenue_aud ?? 0;
  const totalCost = data?.total_cost_usd ?? 0;
  const totalProfit = data?.total_profit_aud ?? 0;
  const totalTokensM = (data?.token_usage ?? []).reduce((s, t) => s + t.total_tokens, 0) / 1_000_000;
  const targetProgress = (totalRevenue / MONTHLY_TARGET) * 100;

  const modelCosts = (data?.model_costs ?? []).map(tokenUsageToModelCost);

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Finance</h1>
            <p className="text-sm text-cortex-muted mt-0.5">Revenue, costs, and projections</p>
          </div>
          <Select value={period} onValueChange={(v) => setPeriod(v as typeof period)}>
            <SelectTrigger className="w-28">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">7 days</SelectItem>
              <SelectItem value="30d">30 days</SelectItem>
              <SelectItem value="90d">90 days</SelectItem>
              <SelectItem value="1y">1 year</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            {
              label: "Revenue (MTD)",
              value: isLoading ? null : formatCurrency(totalRevenue, "AUD"),
              icon: DollarSign,
            },
            {
              label: "Costs (MTD)",
              value: isLoading ? null : formatCurrency(totalCost, "USD"),
              icon: TrendingUp,
            },
            {
              label: "Profit (MTD)",
              value: isLoading ? null : formatCurrency(totalProfit, "AUD"),
              icon: TrendingDown,
            },
            {
              label: "Tokens (MTD)",
              value: isLoading ? null : formatTokens(totalTokensM * 1_000_000),
              icon: Cpu,
            },
          ].map((card) => (
            <div key={card.label} className="cortex-card">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium uppercase tracking-widest text-cortex-muted">{card.label}</span>
                <card.icon className="h-4 w-4 text-cortex-muted" />
              </div>
              {card.value === null ? (
                <Skeleton className="h-7 w-28" />
              ) : (
                <p className="text-xl font-bold font-mono text-cortex-text">{card.value}</p>
              )}
            </div>
          ))}
        </div>

        {/* Monthly target progress */}
        {!isLoading && (
          <div className="cortex-card">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-cortex-accent" />
                <span className="text-sm font-semibold text-cortex-text">Monthly Target Progress</span>
              </div>
              <span className="text-xs font-mono text-cortex-muted">
                {formatCurrency(totalRevenue, "AUD")} / {formatCurrency(MONTHLY_TARGET, "AUD")}
              </span>
            </div>
            <Progress
              value={Math.min(targetProgress, 100)}
              className="h-2.5"
              indicatorClassName={
                targetProgress >= 100
                  ? "bg-cortex-success"
                  : targetProgress >= 75
                  ? "bg-cortex-warning"
                  : "bg-cortex-accent"
              }
            />
            <p className="mt-1.5 text-xs text-cortex-muted">
              {formatPercent(Math.min(targetProgress, 100), 1)} of target{" "}
              {targetProgress >= 100 && <Badge variant="success" className="text-[10px] ml-1">Target Hit!</Badge>}
            </p>
          </div>
        )}

        {/* Charts */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          {/* Revenue chart */}
          <div className="xl:col-span-2 cortex-card">
            <div className="section-header">
              <h2 className="text-sm font-semibold text-cortex-text">Revenue vs Costs vs Profit</h2>
              <span className="text-xs text-cortex-muted">{period}</span>
            </div>
            {isLoading ? (
              <Skeleton className="h-[280px] w-full" />
            ) : (
              <RevenueBreakdown data={data?.revenue_history ?? []} />
            )}
          </div>

          {/* LLM cost breakdown */}
          <div className="cortex-card">
            <div className="section-header">
              <h2 className="text-sm font-semibold text-cortex-text">LLM Cost by Model</h2>
            </div>
            {isLoading ? (
              <Skeleton className="h-[220px] w-full" />
            ) : (
              <CostBreakdown data={modelCosts} />
            )}
          </div>
        </div>

        {/* Token usage table */}
        <div className="cortex-card">
          <h2 className="text-sm font-semibold text-cortex-text mb-4">Token Usage by Model</h2>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex gap-4">
                  <Skeleton className="h-4 flex-1" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-16" />
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-cortex-border overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-cortex-bg/30 border-b border-cortex-border">
                  <tr>
                    <th className="text-left px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Model</th>
                    <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Tokens</th>
                    <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Cost (USD)</th>
                    <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">% of Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cortex-border">
                  {(data?.token_usage ?? []).map((t) => (
                    <tr key={`${t.provider}-${t.model}`} className="hover:bg-cortex-border/20 transition-colors">
                      <td className="px-4 py-2.5 font-medium text-cortex-text">
                        <span className="text-cortex-muted text-xs mr-1">{t.provider}/</span>{t.model}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono text-cortex-muted">{formatTokens(t.total_tokens)}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-cortex-text">{formatCurrency(t.cost_usd, "USD")}</td>
                      <td className="px-4 py-2.5 text-right font-mono text-cortex-muted">{t.percent_of_total.toFixed(1)}%</td>
                    </tr>
                  ))}
                  {(data?.token_usage ?? []).length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-4 py-6 text-center text-xs text-cortex-muted">No cost records yet</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
