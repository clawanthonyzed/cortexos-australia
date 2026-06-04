"use client";

import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { StatusDot } from "@/components/ui/status-dot";
import { formatDistanceToNow, format } from "date-fns";
import { RotateCcw, XCircle, Cpu } from "lucide-react";
import type { Task } from "@/types/task";
import { api } from "@/lib/api";
import { useState } from "react";

interface TaskDetailProps {
  task: Task | null;
  open: boolean;
  onClose: () => void;
  onUpdated: (task: Task) => void;
}

const STATUS_DOT_MAP: Record<string, "idle" | "running" | "paused" | "error" | "stopped" | "active" | "draft" | "archived"> = {
  queued: "idle",
  running: "running",
  completed: "active",
  failed: "error",
  cancelled: "stopped",
  paused: "paused",
};

function MetaRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <span className="text-xs text-cortex-muted shrink-0 w-32">{label}</span>
      <span className="text-xs text-cortex-text text-right">{value}</span>
    </div>
  );
}

export function TaskDetail({ task, open, onClose, onUpdated }: TaskDetailProps) {
  const [loading, setLoading] = useState<string | null>(null);

  if (!task) return null;

  const handleCancel = async () => {
    setLoading("cancel");
    try {
      const res = await api.post(`/api/v1/tasks/${task.id}/cancel`);
      onUpdated(res.data);
    } finally {
      setLoading(null);
    }
  };

  const handleRetry = async () => {
    setLoading("retry");
    try {
      const res = await api.post(`/api/v1/tasks/${task.id}/retry`);
      onUpdated(res.data);
    } finally {
      setLoading(null);
    }
  };

  const canCancel = ["queued", "running"].includes(task.status);
  const canRetry = ["failed", "cancelled"].includes(task.status);

  return (
    <Sheet open={open} onOpenChange={(o) => !o && onClose()}>
      <SheetContent
        side="right"
        className="w-[420px] bg-cortex-surface border-cortex-border text-cortex-text overflow-y-auto"
      >
        <SheetHeader>
          <SheetTitle className="text-cortex-text text-base pr-6">{task.title}</SheetTitle>
        </SheetHeader>

        <div className="mt-4 space-y-4">
          {/* Status + priority */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <StatusDot status={STATUS_DOT_MAP[task.status] ?? "idle"} />
              <span className="text-sm capitalize text-cortex-text">{task.status}</span>
            </div>
            <Badge variant="outline" className="border-cortex-border text-cortex-muted text-xs">
              {task.priority}
            </Badge>
          </div>

          {/* Description */}
          {task.description && (
            <p className="text-sm text-cortex-muted leading-relaxed">{task.description}</p>
          )}

          <Separator className="bg-cortex-border" />

          {/* Metadata */}
          <div className="divide-y divide-cortex-border/50">
            <MetaRow label="Task ID" value={
              <span className="font-mono text-cortex-muted">{task.id.slice(0, 8)}…</span>
            } />
            {task.agentId && (
              <MetaRow label="Agent" value={
                <span className="flex items-center gap-1">
                  <Cpu className="h-3 w-3 text-cortex-accent" />
                  {task.agentName ?? task.agentId.slice(0, 8) + "…"}
                </span>
              } />
            )}
            <MetaRow label="Created" value={
              formatDistanceToNow(new Date(task.createdAt), { addSuffix: true })
            } />
            {task.startedAt && (
              <MetaRow
                label="Started"
                value={format(new Date(task.startedAt), "MMM d, HH:mm:ss")}
              />
            )}
            {task.completedAt && (
              <MetaRow
                label="Completed"
                value={format(new Date(task.completedAt), "MMM d, HH:mm:ss")}
              />
            )}
            {task.durationMs && (
              <MetaRow
                label="Duration"
                value={`${(task.durationMs / 1000).toFixed(1)}s`}
              />
            )}
            <MetaRow label="Tokens" value={task.tokensUsed.toLocaleString()} />
            <MetaRow label="Cost" value={`$${task.costUsd.toFixed(4)}`} />
          </div>

          {/* Output */}
          {task.output && Object.keys(task.output).length > 0 && (
            <>
              <Separator className="bg-cortex-border" />
              <div>
                <p className="text-xs font-medium text-cortex-muted uppercase tracking-wider mb-2">
                  Output
                </p>
                <pre className="text-xs text-cortex-text bg-cortex-bg rounded-md p-3 overflow-auto max-h-48 border border-cortex-border">
                  {JSON.stringify(task.output, null, 2)}
                </pre>
              </div>
            </>
          )}

          {/* Error */}
          {task.errorMessage && (
            <>
              <Separator className="bg-cortex-border" />
              <div>
                <p className="text-xs font-medium text-red-400 uppercase tracking-wider mb-2">
                  Error
                </p>
                <div className="text-xs text-red-300 bg-red-950/30 rounded-md p-3 border border-red-900/40">
                  {task.errorMessage}
                </div>
              </div>
            </>
          )}

          {/* Actions */}
          {(canCancel || canRetry) && (
            <>
              <Separator className="bg-cortex-border" />
              <div className="flex gap-2">
                {canCancel && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancel}
                    disabled={loading !== null}
                    className="border-cortex-border gap-1.5"
                  >
                    <XCircle className="h-3.5 w-3.5" />
                    Cancel
                  </Button>
                )}
                {canRetry && (
                  <Button
                    size="sm"
                    onClick={handleRetry}
                    disabled={loading !== null}
                    className="gap-1.5"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    Retry
                  </Button>
                )}
              </div>
            </>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
