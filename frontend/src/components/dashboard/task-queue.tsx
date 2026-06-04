"use client";

import Link from "next/link";
import { Clock, CheckCircle2, XCircle, Loader2, Pause, Circle } from "lucide-react";
import type { Task } from "@/types/task";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRelativeTime, truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface TaskQueueWidgetProps {
  tasks: Task[];
  isLoading?: boolean;
}

function StatusIcon({ status }: { status: Task["status"] }) {
  switch (status) {
    case "running":
      return <Loader2 className="h-3.5 w-3.5 text-cortex-accent animate-spin" />;
    case "completed":
      return <CheckCircle2 className="h-3.5 w-3.5 text-cortex-success" />;
    case "failed":
      return <XCircle className="h-3.5 w-3.5 text-cortex-error" />;
    case "paused":
      return <Pause className="h-3.5 w-3.5 text-cortex-warning" />;
    case "queued":
      return <Clock className="h-3.5 w-3.5 text-cortex-muted" />;
    default:
      return <Circle className="h-3.5 w-3.5 text-cortex-muted" />;
  }
}

const priorityColors = {
  critical: "text-cortex-error",
  high: "text-cortex-warning",
  normal: "text-cortex-muted",
  low: "text-cortex-muted",
};

export function TaskQueueWidget({ tasks, isLoading }: TaskQueueWidgetProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-center gap-2 py-1.5">
            <Skeleton className="h-3.5 w-3.5 rounded-full flex-shrink-0" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-3 w-36" />
              <Skeleton className="h-2.5 w-20" />
            </div>
            <Skeleton className="h-4 w-12 rounded-full" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-0.5">
      {tasks.slice(0, 10).map((task) => (
        <Link
          key={task.id}
          href={`/tasks`}
          className={cn(
            "flex items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors",
            "hover:bg-cortex-border/50 group"
          )}
        >
          <StatusIcon status={task.status} />

          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-cortex-text truncate group-hover:text-cortex-accent transition-colors">
              {truncate(task.title, 48)}
            </p>
            <p className="text-[11px] text-cortex-muted">
              {task.agentName ?? "Unassigned"} · {formatRelativeTime(task.queuedAt)}
            </p>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            {(task.priority === "critical" || task.priority === "high") && (
              <span className={cn("text-[10px] font-semibold uppercase", priorityColors[task.priority])}>
                {task.priority}
              </span>
            )}
            {task.status === "running" && task.progressPercent > 0 && (
              <span className="text-[10px] font-mono text-cortex-accent">
                {task.progressPercent}%
              </span>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}
