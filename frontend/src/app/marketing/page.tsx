"use client";

import useSWR from "swr";
import { Plus, Megaphone, TrendingUp, Users, MousePointerClick, DollarSign } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { fetcher } from "@/lib/api";
import { formatCurrency, formatRelativeTime, formatPercent } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface Campaign {
  id: string;
  name: string;
  type: "email" | "social" | "paid_ads" | "content" | "seo";
  status: "active" | "paused" | "completed" | "draft";
  venture: string;
  platform: string;
  budget: number;
  spent: number;
  impressions: number;
  clicks: number;
  conversions: number;
  revenue: number;
  startedAt: string;
  endedAt: string | null;
}

const statusVariant = {
  active: "success" as const,
  paused: "warning" as const,
  completed: "muted" as const,
  draft: "muted" as const,
};

const typeIcon = {
  email: "✉️",
  social: "📱",
  paid_ads: "💰",
  content: "📝",
  seo: "🔍",
};

export default function MarketingPage() {
  const { data, isLoading } = useSWR<{ campaigns: Campaign[]; total: number }>(
    "/marketing/campaigns",
    fetcher,
    { refreshInterval: 60000 }
  );

  const campaigns = data?.campaigns ?? [];

  const totalSpend = campaigns.reduce((s, c) => s + c.spent, 0);
  const totalRevenue = campaigns.reduce((s, c) => s + c.revenue, 0);
  const totalConversions = campaigns.reduce((s, c) => s + c.conversions, 0);
  const avgCtr = campaigns.length > 0
    ? campaigns.reduce((s, c) => s + (c.impressions > 0 ? c.clicks / c.impressions : 0), 0) / campaigns.length
    : 0;

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Marketing</h1>
            <p className="text-sm text-cortex-muted mt-0.5">Campaigns and attribution</p>
          </div>
          <Button>
            <Plus className="h-4 w-4" />
            New Campaign
          </Button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Spend", value: formatCurrency(totalSpend, "USD", true), icon: DollarSign, color: "text-cortex-warning" },
            { label: "Attributed Revenue", value: formatCurrency(totalRevenue, "AUD", true), icon: TrendingUp, color: "text-cortex-success" },
            { label: "Conversions", value: totalConversions.toLocaleString(), icon: Users, color: "text-cortex-accent" },
            { label: "Avg CTR", value: formatPercent(avgCtr * 100, 2), icon: MousePointerClick, color: "text-cortex-muted" },
          ].map((s) => (
            <div key={s.label} className="cortex-card">
              <div className="flex items-center gap-2 mb-1">
                <s.icon className={cn("h-3.5 w-3.5", s.color)} />
                <span className="text-xs text-cortex-muted">{s.label}</span>
              </div>
              <p className="text-xl font-bold font-mono text-cortex-text">{s.value}</p>
            </div>
          ))}
        </div>

        {/* Campaigns table */}
        {isLoading ? (
          <div className="cortex-card space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-4">
                <Skeleton className="h-4 flex-1" />
                <Skeleton className="h-4 w-16" />
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        ) : campaigns.length === 0 ? (
          <EmptyState
            icon={Megaphone}
            title="No campaigns yet"
            description="Create your first marketing campaign to track attribution and ROI"
          />
        ) : (
          <div className="rounded-lg border border-cortex-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-cortex-bg/30 border-b border-cortex-border">
                <tr>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Campaign</th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-cortex-muted hidden sm:table-cell">Type</th>
                  <th className="text-left px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Status</th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-cortex-muted hidden md:table-cell">Impressions</th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-cortex-muted hidden lg:table-cell">CTR</th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Revenue</th>
                  <th className="text-right px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-cortex-muted hidden md:table-cell">ROAS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-cortex-border">
                {campaigns.map((c) => {
                  const ctr = c.impressions > 0 ? (c.clicks / c.impressions) * 100 : 0;
                  const roas = c.spent > 0 ? c.revenue / c.spent : 0;
                  return (
                    <tr key={c.id} className="hover:bg-cortex-border/20 transition-colors cursor-pointer">
                      <td className="px-4 py-3">
                        <p className="font-medium text-cortex-text">{c.name}</p>
                        <p className="text-[11px] text-cortex-muted">{c.venture} · {c.platform}</p>
                      </td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        <span className="text-sm">{typeIcon[c.type] ?? "📊"}</span>
                        <span className="ml-1 text-xs text-cortex-muted capitalize">{c.type.replace("_", " ")}</span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={statusVariant[c.status]} className="text-[10px] py-0 px-1.5">
                          {c.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-cortex-muted hidden md:table-cell text-xs">
                        {c.impressions.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-cortex-muted hidden lg:table-cell text-xs">
                        {formatPercent(ctr, 2)}
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-cortex-success text-xs">
                        {formatCurrency(c.revenue, "AUD", true)}
                      </td>
                      <td className="px-4 py-3 text-right hidden md:table-cell">
                        <span className={cn(
                          "text-xs font-mono font-semibold",
                          roas >= 3 ? "text-cortex-success" :
                          roas >= 1 ? "text-cortex-warning" :
                          "text-cortex-error"
                        )}>
                          {roas.toFixed(2)}x
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
    </AppShell>
  );
}
