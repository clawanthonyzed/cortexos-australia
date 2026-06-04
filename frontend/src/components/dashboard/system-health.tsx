"use client";

import { Database, Server, Wifi, Activity, AlertCircle, CheckCircle2 } from "lucide-react";
import type { SystemHealth } from "@/store/system-store";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface SystemHealthProps {
  health: SystemHealth | null;
  isLoading?: boolean;
}

interface HealthItem {
  label: string;
  healthy: boolean;
  icon: React.ElementType;
  detail?: string;
}

export function SystemHealthWidget({ health, isLoading }: SystemHealthProps) {
  if (isLoading || !health) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-2 w-full rounded-full" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <Skeleton className="h-4 w-4 rounded" />
            <Skeleton className="h-3 flex-1" />
            <Skeleton className="h-3.5 w-3.5 rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  const healthItems: HealthItem[] = [
    {
      label: "API Server",
      healthy: health.apiLatencyMs < 500,
      icon: Server,
      detail: `${health.apiLatencyMs}ms`,
    },
    {
      label: "Database",
      healthy: health.dbHealthy,
      icon: Database,
      detail: health.dbHealthy ? "Connected" : "Disconnected",
    },
    {
      label: "WebSocket",
      healthy: health.wsHealthy,
      icon: Wifi,
      detail: health.wsHealthy ? "Live" : "Offline",
    },
    {
      label: "Agent Service",
      healthy: health.agentServiceHealthy,
      icon: Activity,
      detail: `Queue: ${health.queueDepth}`,
    },
  ];

  const healthColor =
    health.overallPercent >= 99
      ? "bg-cortex-success"
      : health.overallPercent >= 95
      ? "bg-cortex-warning"
      : "bg-cortex-error";

  return (
    <div className="space-y-3">
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-cortex-muted">Overall Health</span>
          <span
            className={cn(
              "text-xs font-mono font-semibold",
              health.overallPercent >= 99
                ? "text-cortex-success"
                : health.overallPercent >= 95
                ? "text-cortex-warning"
                : "text-cortex-error"
            )}
          >
            {health.overallPercent.toFixed(2)}%
          </span>
        </div>
        <Progress
          value={health.overallPercent}
          indicatorClassName={healthColor}
          className="h-1.5"
        />
      </div>

      <div className="space-y-2">
        {healthItems.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="flex items-center gap-2.5">
              <Icon className="h-3.5 w-3.5 text-cortex-muted flex-shrink-0" />
              <span className="flex-1 text-xs text-cortex-text">{item.label}</span>
              <span className="text-[11px] font-mono text-cortex-muted">{item.detail}</span>
              {item.healthy ? (
                <CheckCircle2 className="h-3.5 w-3.5 text-cortex-success flex-shrink-0" />
              ) : (
                <AlertCircle className="h-3.5 w-3.5 text-cortex-error flex-shrink-0" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
