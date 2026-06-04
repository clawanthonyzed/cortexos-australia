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
import { formatCurrency, formatPercent, formatTokens, getDelta } from "@/lib/utils";
import { cn } from "@/lib/utils";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function FinancePage() {
  const [period, setPeriod] = useState<"7d" | "30d" | "90d" | "1y">("30d");
  const { data, isLoading } = useFinance({ period });

  const summary = data?.summary;

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
              value: isLoading ? null : formatCurrency(summary?.revenueThisMonthAud ?? 0, "AUD"),
              delta: summary?.revenueGrowthPercent,
              icon: DollarSign,
              good: true,
            },
            {
              label: "Costs (MTD)",
              value: isLoading ? null : formatCurrency(summary?.costsThisMonthUsd ?? 0, "USD"),
              delta: summary?.costsGrowthPercent,
              icon: TrendingUp,
              good: false,
            },
            {
              label: "Profit (MTD)",
              value: isLoading ? null : formatCurrency(summary?.profitThisMonthAud ?? 0, "AUD"),
              delta: summary ? getDelta(summary.profitThisMonthAud, summary.profitThisMonthAud / 1.2) : undefined,
              icon: TrendingDown,
              good: true,
            },
            {
              label: "Tokens (MTD)",
              value: isLoading ? null : formatTokens((summary?.tokenUsageMonthM ?? 0) * 1_000_000),
              delta: undefined,
              icon: Cpu,
              good: false,
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
              {card.delta !== undefined && (
                <div className={cn(
                  "flex items-center gap-1 mt-1 text-xs font-medium",
                  (card.good ? card.delta >= 0 : card.delta <= 0)
                    ? "text-cortex-success"
                    : "text-cortex-error"
                )}>
                  {(card.good ? card.delta >= 0 : card.delta <= 0)
                    ? <ArrowUpRight className="h-3 w-3" />
                    : <ArrowDownRight className="h-3 w-3" />}
                  {Math.abs(card.delta).toFixed(1)}% vs last period
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Monthly target progress */}
        {summary && (
          <div className="cortex-card">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4 text-cortex-accent" />
                <span className="text-sm font-semibold text-cortex-text">Monthly Target Progress</span>
              </div>
              <span className="text-xs font-mono text-cortex-muted">
                {formatCurrency(summary.revenueThisMonthAud, "AUD")} / {formatCurrency(summary.monthlyTarget, "AUD")}
              </span>
            </div>
            <Progress
              value={Math.min(summary.targetProgressPercent, 100)}
              className="h-2.5"
              indicatorClassName={
                summary.targetProgressPercent >= 100
                  ? "bg-cortex-success"
                  : summary.targetProgressPercent >= 75
                  ? "bg-cortex-warning"
                  : "bg-cortex-accent"
              }
            />
            <p className="mt-1.5 text-xs text-cortex-muted">
              {formatPercent(Math.min(summary.targetProgressPercent, 100), 1)} of target{" "}
              {summary.targetProgressPercent >= 100 && <Badge variant="success" className="text-[10px] ml-1">Target Hit!</Badge>}
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
              <RevenueBreakdown data={data?.revenueHistory ?? []} />
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
              <CostBreakdown data={data?.modelCosts ?? []} />
            )}
          </div>
        </div>

        {/* Venture breakdown table */}
        <div className="cortex-card">
          <h2 className="text-sm font-semibold text-cortex-text mb-4">Revenue by Venture</h2>
          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex gap-4">
                  <Skeleton className="h-4 flex-1" />
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-4 w-16" />
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-cortex-border overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-cortex-bg/30 border-b border-cortex-border">
                  <tr>
                    <th className="text-left px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Venture</th>
                    <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Revenue MTD</th>
                    <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Costs MTD</th>
                    <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Profit</th>
                    <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Growth</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-cortex-border">
                  {(data?.ventureBreakdown ?? []).map((v) => {
                    const isPositive = v.growthPercent >= 0;
                    return (
                      <tr key={v.venture} className="hover:bg-cortex-border/20 transition-colors">
                        <td className="px-4 py-2.5 font-medium text-cortex-text capitalize">{v.venture}</td>
                        <td className="px-4 py-2.5 text-right font-mono text-cortex-text">
                          {formatCurrency(v.revenueThisMonth, "AUD", true)}
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono text-cortex-muted">
                          {formatCurrency(v.costsThisMonth, "USD", true)}
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono text-cortex-success">
                          {formatCurrency(v.profitThisMonth, "AUD", true)}
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <span className={cn(
                            "flex items-center justify-end gap-1 text-xs font-medium",
                            isPositive ? "text-cortex-success" : "text-cortex-error"
                          )}>
                            {isPositive
                              ? <ArrowUpRight className="h-3 w-3" />
                              : <ArrowDownRight className="h-3 w-3" />}
                            {Math.abs(v.growthPercent).toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
