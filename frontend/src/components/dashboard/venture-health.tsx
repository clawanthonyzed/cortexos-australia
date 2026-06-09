"use client";

import useSWR from "swr";
import { TrendingUp, TrendingDown, Minus, Activity } from "lucide-react";
import { fetcher } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

interface VentureHealth {
  slug: string;
  name: string;
  manager: string;
  category: string;
  healthScore: number;
  status: "healthy" | "warning" | "critical" | "inactive";
  tasksLast7d: number;
  successRate: number;
  agentCount: number;
  lastActivityAt: string | null;
}

interface VentureHealthResponse {
  empireHealthScore: number;
  summary: { healthy: number; warning: number; critical: number };
  ventures: VentureHealth[];
  generatedAt: string;
}

const statusConfig = {
  healthy: { color: "text-cortex-success", bg: "bg-cortex-success/10", bar: "bg-cortex-success" },
  warning: { color: "text-amber-400", bg: "bg-amber-400/10", bar: "bg-amber-400" },
  critical: { color: "text-cortex-error", bg: "bg-cortex-error/10", bar: "bg-cortex-error" },
  inactive: { color: "text-cortex-muted", bg: "bg-cortex-muted/10", bar: "bg-cortex-muted/40" },
};

function ScoreBar({ score, status }: { score: number; status: VentureHealth["status"] }) {
  const cfg = statusConfig[status];
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full bg-cortex-border overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${cfg.bar}`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className={`text-xs font-mono font-bold w-8 text-right ${cfg.color}`}>{score}</span>
    </div>
  );
}

export function VentureHealthMatrix() {
  const { data, isLoading } = useSWR<VentureHealthResponse>(
    "/dashboard/venture-health",
    fetcher,
    { refreshInterval: 60_000 }
  );

  if (isLoading) {
    return (
      <div className="rounded-lg border border-cortex-border bg-cortex-surface p-4 space-y-3">
        <Skeleton className="h-5 w-40" />
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) return null;

  const topVentures = data.ventures.slice(0, 12);

  return (
    <div className="rounded-lg border border-cortex-border bg-cortex-surface p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-cortex-accent" />
          <h3 className="text-sm font-semibold text-cortex-text">Empire Health</h3>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="text-cortex-success font-mono font-bold">{data.summary.healthy} healthy</span>
          <span className="text-amber-400 font-mono font-bold">{data.summary.warning} warning</span>
          <span className="text-cortex-error font-mono font-bold">{data.summary.critical} critical</span>
          <span className="ml-2 text-cortex-muted font-mono">
            Score: <span className="text-cortex-text font-bold">{data.empireHealthScore}</span>/100
          </span>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {topVentures.map((v) => {
          const cfg = statusConfig[v.status];
          return (
            <div
              key={v.slug}
              className={`rounded-md border border-cortex-border p-3 space-y-2 ${cfg.bg}`}
            >
              <div className="flex items-start justify-between gap-1">
                <div>
                  <p className="text-xs font-semibold text-cortex-text leading-tight">{v.name}</p>
                  <p className="text-[10px] text-cortex-muted mt-0.5">{v.manager} · {v.category}</p>
                </div>
                <span className={`text-[10px] font-semibold uppercase tracking-wide ${cfg.color}`}>
                  {v.status}
                </span>
              </div>
              <ScoreBar score={v.healthScore} status={v.status} />
              <div className="flex items-center justify-between text-[10px] text-cortex-muted">
                <span>{v.tasksLast7d} tasks/7d</span>
                <span>{v.successRate.toFixed(0)}% success</span>
                <span>{v.agentCount} agent{v.agentCount !== 1 ? "s" : ""}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
