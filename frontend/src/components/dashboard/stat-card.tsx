import type { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
  title: string;
  value: string;
  delta?: number;
  deltaLabel?: string;
  icon: LucideIcon;
  iconColor?: "accent" | "success" | "warning" | "error" | "muted";
  trend?: "up" | "down" | "neutral";
  isLoading?: boolean;
  subtitle?: string;
}

const iconColorClasses = {
  accent: "bg-cortex-accent/15 text-cortex-accent",
  success: "bg-cortex-success/15 text-cortex-success",
  warning: "bg-cortex-warning/15 text-cortex-warning",
  error: "bg-cortex-error/15 text-cortex-error",
  muted: "bg-cortex-border text-cortex-muted",
};

export function StatCard({
  title,
  value,
  delta,
  deltaLabel,
  icon: Icon,
  iconColor = "accent",
  trend,
  isLoading,
  subtitle,
}: StatCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-lg border border-cortex-border bg-cortex-surface p-4">
        <div className="flex items-start justify-between mb-3">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-9 w-9 rounded-lg" />
        </div>
        <Skeleton className="h-7 w-32 mb-1" />
        <Skeleton className="h-3.5 w-20" />
      </div>
    );
  }

  const effectiveTrend = trend ?? (delta !== undefined ? (delta > 0 ? "up" : delta < 0 ? "down" : "neutral") : undefined);

  return (
    <div className="group rounded-lg border border-cortex-border bg-cortex-surface p-4 transition-colors duration-150 hover:border-cortex-accent/30">
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs font-medium uppercase tracking-widest text-cortex-muted">{title}</p>
        <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg", iconColorClasses[iconColor])}>
          <Icon className="h-4.5 w-4.5" aria-hidden="true" />
        </div>
      </div>
      <p className="mb-1 text-2xl font-bold text-cortex-text font-mono tracking-tight">{value}</p>
      <div className="flex items-center gap-1.5">
        {effectiveTrend !== undefined && delta !== undefined && (
          <>
            {effectiveTrend === "up" && <TrendingUp className="h-3 w-3 text-cortex-success" />}
            {effectiveTrend === "down" && <TrendingDown className="h-3 w-3 text-cortex-error" />}
            {effectiveTrend === "neutral" && <Minus className="h-3 w-3 text-cortex-muted" />}
            <span
              className={cn(
                "text-xs font-medium",
                effectiveTrend === "up" ? "text-cortex-success" :
                effectiveTrend === "down" ? "text-cortex-error" :
                "text-cortex-muted"
              )}
            >
              {Math.abs(delta).toFixed(1)}%
            </span>
          </>
        )}
        {deltaLabel && (
          <span className="text-xs text-cortex-muted">{deltaLabel}</span>
        )}
        {subtitle && !delta && (
          <span className="text-xs text-cortex-muted">{subtitle}</span>
        )}
      </div>
    </div>
  );
}
