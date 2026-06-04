"use client";

import { useState } from "react";
import {
  CheckCircle2, XCircle, Loader2, Clock, Pause, Circle,
  StopCircle, RotateCcw, ChevronRight
} from "lucide-react";
import type { Task } from "@/types/task";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { useCancelTask, useRetryTask } from "@/hooks/use-tasks";
import { formatCurrency, formatDuration, formatRelativeTime, truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { mutate } from "swr";

interface TaskRowProps {
  task: Task;
  onSelect?: (task: Task) => void;
}

const statusConfig: Record<Task["status"], { icon: React.ElementType; color: string; label: string }> = {
  queued: { icon: Clock, color: "text-cortex-muted", label: "Queued" },
  running: { icon: Loader2, color: "text-cortex-accent", label: "Running" },
  completed: { icon: CheckCircle2, color: "text-cortex-success", label: "Completed" },
  failed: { icon: XCircle, color: "text-cortex-error", label: "Failed" },
  cancelled: { icon: StopCircle, color: "text-cortex-muted", label: "Cancelled" },
  paused: { icon: Pause, color: "text-cortex-warning", label: "Paused" },
};

const priorityVariant = {
  critical: "error" as const,
  high: "warning" as const,
  normal: "muted" as const,
  low: "muted" as const,
};

export function TaskRow({ task, onSelect }: TaskRowProps) {
  const [expanded, setExpanded] = useState(false);
  const { trigger: cancelTask, isMutating: cancelling } = useCancelTask(task.id);
  const { trigger: retryTask, isMutating: retrying } = useRetryTask(task.id);

  const statusCfg = statusConfig[task.status];
  const Icon = statusCfg.icon;

  const handleCancel = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await cancelTask();
      await mutate((key: string) => key.startsWith("/tasks"));
      toast.success("Task cancelled");
    } catch {
      toast.error("Failed to cancel task");
    }
  };

  const handleRetry = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await retryTask();
      await mutate((key: string) => key.startsWith("/tasks"));
      toast.success("Task queued for retry");
    } catch {
      toast.error("Failed to retry task");
    }
  };

  return (
    <div
      className={cn(
        "group border-b border-cortex-border last:border-0",
        "hover:bg-cortex-border/20 transition-colors cursor-pointer"
      )}
      onClick={() => {
        setExpanded(!expanded);
        onSelect?.(task);
      }}
    >
      <div className="flex items-center gap-3 px-4 py-3">
        {/* Status icon */}
        <Icon
          className={cn(
            "h-4 w-4 flex-shrink-0",
            statusCfg.color,
            task.status === "running" && "animate-spin"
          )}
        />

        {/* Title & agent */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-cortex-text truncate">{task.title}</p>
          <p className="text-xs text-cortex-muted">
            {task.agentName ?? "Unassigned"} · {formatRelativeTime(task.queuedAt)}
          </p>
        </div>

        {/* Progress (running only) */}
        {task.status === "running" && task.progressPercent > 0 && (
          <div className="hidden sm:flex flex-col items-end gap-1 w-24">
            <span className="text-xs font-mono text-cortex-accent">{task.progressPercent}%</span>
            <Progress value={task.progressPercent} className="h-1" />
          </div>
        )}

        {/* Duration */}
        {task.durationMs && (
          <span className="hidden sm:block text-xs font-mono text-cortex-muted w-14 text-right">
            {formatDuration(task.durationMs)}
          </span>
        )}

        {/* Cost */}
        <span className="hidden md:block text-xs font-mono text-cortex-muted w-16 text-right">
          {task.costUsd > 0 ? formatCurrency(task.costUsd, "USD") : "-"}
        </span>

        {/* Priority */}
        {task.priority !== "normal" && (
          <Badge variant={priorityVariant[task.priority]} className="text-[10px] py-0 px-1.5 hidden sm:flex">
            {task.priority}
          </Badge>
        )}

        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
          {task.status === "running" || task.status === "queued" ? (
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label="Cancel task"
              onClick={handleCancel}
              disabled={cancelling}
              className="hover:text-cortex-error hover:bg-cortex-error/10 h-6 w-6"
            >
              <StopCircle className="h-3.5 w-3.5" />
            </Button>
          ) : null}
          {task.status === "failed" ? (
            <Button
              variant="ghost"
              size="icon-sm"
              aria-label="Retry task"
              onClick={handleRetry}
              disabled={retrying}
              className="hover:text-cortex-success hover:bg-cortex-success/10 h-6 w-6"
            >
              <RotateCcw className="h-3.5 w-3.5" />
            </Button>
          ) : null}
        </div>

        <ChevronRight
          className={cn(
            "h-4 w-4 text-cortex-muted transition-transform flex-shrink-0",
            expanded && "rotate-90"
          )}
        />
      </div>

      {/* Expanded steps */}
      {expanded && task.steps.length > 0 && (
        <div className="px-4 pb-3 border-t border-cortex-border bg-cortex-bg/30">
          <div className="pt-3 space-y-1.5 ml-7">
            {task.steps.map((step) => (
              <div key={step.id} className="flex items-center gap-2">
                {step.status === "completed" ? (
                  <CheckCircle2 className="h-3 w-3 text-cortex-success flex-shrink-0" />
                ) : step.status === "running" ? (
                  <Loader2 className="h-3 w-3 text-cortex-accent animate-spin flex-shrink-0" />
                ) : step.status === "failed" ? (
                  <XCircle className="h-3 w-3 text-cortex-error flex-shrink-0" />
                ) : (
                  <Circle className="h-3 w-3 text-cortex-muted flex-shrink-0" />
                )}
                <span className="text-xs text-cortex-text flex-1 truncate">{step.name}</span>
                {step.durationMs && (
                  <span className="text-[10px] font-mono text-cortex-muted">{formatDuration(step.durationMs)}</span>
                )}
              </div>
            ))}
          </div>
          {task.errorMessage && (
            <div className="mt-2 ml-7 rounded-md bg-cortex-error/10 border border-cortex-error/20 px-3 py-2">
              <p className="text-xs text-cortex-error font-mono">{task.errorMessage}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
