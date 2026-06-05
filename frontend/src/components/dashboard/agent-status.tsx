"use client";

import Link from "next/link";
import { Bot, ArrowRight } from "lucide-react";
import type { Agent } from "@/types/agent";
import { StatusDot } from "@/components/ui/status-dot";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface AgentStatusWidgetProps {
  agents: Agent[];
  isLoading?: boolean;
}

const statusBadgeVariant = (status: Agent["status"]) => {
  switch (status) {
    case "running": return "success" as const;
    case "paused": return "warning" as const;
    case "error": return "error" as const;
    default: return "muted" as const;
  }
};

export function AgentStatusWidget({ agents, isLoading }: AgentStatusWidgetProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 py-2">
            <Skeleton className="h-7 w-7 rounded-lg" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-3.5 w-28" />
              <Skeleton className="h-3 w-40" />
            </div>
            <Skeleton className="h-5 w-14 rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  const sortedAgents = [...agents]
    .sort((a, b) => {
      const order = { running: 0, paused: 1, error: 2, idle: 3, stopped: 4 };
      return (order[a.status] ?? 5) - (order[b.status] ?? 5);
    })
    .slice(0, 8);

  return (
    <div className="space-y-1">
      {sortedAgents.map((agent) => (
        <Link
          key={agent.id}
          href={`/agents/${agent.id}`}
          className={cn(
            "flex items-center gap-3 rounded-md px-2 py-1.5 transition-colors",
            "hover:bg-cortex-border/50 group"
          )}
        >
          <div className="relative flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-cortex-border">
            <Bot className="h-3.5 w-3.5 text-cortex-muted" />
            <StatusDot
              status={agent.status}
              size="sm"
              pulse={agent.status === "running"}
              className="absolute -bottom-0.5 -right-0.5"
            />
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-cortex-text truncate group-hover:text-cortex-accent transition-colors">
              {agent.name}
            </p>
            <p className="text-[11px] text-cortex-muted truncate">
              {agent.status === "running" && agent.currentTask ? (
                <span
                  className="t-shimmer"
                  data-text={truncate(agent.currentTask, 42)}
                >
                  {truncate(agent.currentTask, 42)}
                </span>
              ) : agent.currentTask ? (
                truncate(agent.currentTask, 42)
              ) : (
                agent.purpose
              )}
            </p>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="text-[10px] font-mono text-cortex-muted hidden sm:block">
              {formatCurrency(agent.metrics.totalCostUsd, "USD", true)}
            </span>
            <Badge variant={statusBadgeVariant(agent.status)} className="text-[10px] py-0 px-1.5">
              {agent.status}
            </Badge>
          </div>
        </Link>
      ))}

      {agents.length > 8 && (
        <Link
          href="/agents"
          className="flex items-center justify-center gap-1.5 py-2 text-xs text-cortex-muted hover:text-cortex-accent transition-colors"
        >
          View all {agents.length} agents
          <ArrowRight className="h-3 w-3" />
        </Link>
      )}
    </div>
  );
}
