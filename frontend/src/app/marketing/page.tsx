"use client";

import useSWR from "swr";
import { Megaphone, TrendingUp, DollarSign, BarChart3, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { fetcher } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { mutate } from "swr";
import type { FinanceDashboard } from "@/types/finance";

export default function MarketingPage() {
  const { data: finance, isLoading } = useSWR<FinanceDashboard>(
    "/finance",
    fetcher,
    { refreshInterval: 60000 }
  );

  const byPlatform = finance?.revenue_by_platform ?? [];
  const monthlyTrend = finance?.monthly_trend ?? [];
  const recentMonths = monthlyTrend.slice(-3);

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Marketing</h1>
            <p className="text-sm text-cortex-muted mt-0.5">Revenue attribution by platform</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => mutate("/finance")}>
            <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
            Refresh
          </Button>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="cortex-card space-y-2">
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-6 w-28" />
              </div>
            ))
          ) : (
            <>
              <div className="cortex-card">
                <div className="flex items-center gap-2 mb-1">
                  <DollarSign className="h-3.5 w-3.5 text-cortex-success" />
                  <span className="text-xs text-cortex-muted">Total Revenue</span>
                </div>
                <p className="text-xl font-bold font-mono text-cortex-text">
                  {formatCurrency(finance?.total_revenue_aud ?? 0, "AUD", true)}
                </p>
              </div>
              <div className="cortex-card">
                <div className="flex items-center gap-2 mb-1">
                  <TrendingUp className="h-3.5 w-3.5 text-cortex-accent" />
                  <span className="text-xs text-cortex-muted">Total Sales</span>
                </div>
                <p className="text-xl font-bold font-mono text-cortex-text">
                  {(finance?.total_sales ?? 0).toLocaleString()}
                </p>
              </div>
              <div className="cortex-card">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart3 className="h-3.5 w-3.5 text-cortex-warning" />
                  <span className="text-xs text-cortex-muted">Avg Order</span>
                </div>
                <p className="text-xl font-bold font-mono text-cortex-text">
                  {formatCurrency(finance?.avg_order_value_aud ?? 0, "AUD", true)}
                </p>
              </div>
            </>
          )}
        </div>

        {/* Revenue by platform */}
        <div className="cortex-card">
          <div className="flex items-center gap-2 mb-4">
            <Megaphone className="h-4 w-4 text-cortex-muted" />
            <span className="text-sm font-semibold text-cortex-text">Revenue by Platform</span>
          </div>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 flex-1" />
                  <Skeleton className="h-4 w-16" />
                </div>
              ))}
            </div>
          ) : byPlatform.length === 0 ? (
            <p className="text-sm text-cortex-muted py-4 text-center">No platform data yet. Connect Gumroad, Etsy, or LemonSqueezy in Settings.</p>
          ) : (
            <div className="space-y-3">
              {byPlatform.map((p) => {
                const maxRev = Math.max(...byPlatform.map((x) => x.revenue_aud), 1);
                const pct = (p.revenue_aud / maxRev) * 100;
                return (
                  <div key={p.platform} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-cortex-text capitalize">{p.platform}</span>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-cortex-muted">{p.sales_count} sales</span>
                        <span className="font-mono font-semibold text-cortex-success text-sm">
                          {formatCurrency(p.revenue_aud, "AUD", true)}
                        </span>
                      </div>
                    </div>
                    <div className="h-1.5 w-full rounded-full bg-cortex-border overflow-hidden">
                      <div
                        className="h-full rounded-full bg-cortex-success/60 transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Monthly trend */}
        {recentMonths.length > 0 && (
          <div className="cortex-card">
            <p className="text-sm font-semibold text-cortex-text mb-4">Recent Monthly Trend</p>
            <div className="grid grid-cols-3 gap-3">
              {recentMonths.map((m) => (
                <div key={m.month} className="rounded-lg bg-cortex-bg/30 p-3 text-center">
                  <p className="text-xs text-cortex-muted mb-1">{m.month}</p>
                  <p className="text-sm font-bold font-mono text-cortex-success">
                    {formatCurrency(m.revenue_aud, "AUD", true)}
                  </p>
                  <p className="text-xs text-cortex-muted mt-0.5">{m.sales_count} sales</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
