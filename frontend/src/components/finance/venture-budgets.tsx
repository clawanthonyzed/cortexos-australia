"use client";

import useSWR from "swr";
import { Skeleton } from "@/components/ui/skeleton";
import { fetcher } from "@/lib/api";

interface BudgetRow {
  key: string;
  name: string;
  limit_usd: number;
  spent_usd: number;
  percent: number | null;
}

/** This month's AI spend vs limit per venture, from the Spending Gate (2026-10-10). */
export function VentureBudgets() {
  const { data, isLoading } = useSWR<{ month: string | null; ventures: BudgetRow[] }>("/finance/budgets", fetcher, {
    refreshInterval: 60000,
  });

  return (
    <div className="cortex-card">
      <div className="section-header">
        <h2 className="text-sm font-semibold text-cortex-text">AI spend vs budget by venture</h2>
        <span className="text-xs text-cortex-muted">{data?.month ?? ""} · Spending Gate · USD</span>
      </div>
      {isLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <ul className="space-y-3">
          {(data?.ventures ?? []).map((v) => {
            const pct = Math.min(v.percent ?? 0, 100);
            const tone = pct >= 90 ? "bg-cortex-error" : pct >= 60 ? "bg-cortex-warning" : "bg-cortex-success";
            return (
              <li key={v.key} className="space-y-1">
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="text-cortex-text truncate">{v.name}</span>
                  <span className="font-mono text-xs text-cortex-muted tabular-nums shrink-0">
                    ${v.spent_usd.toFixed(v.spent_usd < 0.01 ? 4 : 2)} / ${v.limit_usd.toFixed(0)} · {(v.percent ?? 0).toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-cortex-border overflow-hidden">
                  <div className={`h-full rounded-full ${tone}`} style={{ width: `${Math.max(pct, 0.5)}%` }} />
                </div>
              </li>
            );
          })}
          {(data?.ventures ?? []).length === 0 && <li className="text-sm text-cortex-muted">No budgets found.</li>}
        </ul>
      )}
    </div>
  );
}
