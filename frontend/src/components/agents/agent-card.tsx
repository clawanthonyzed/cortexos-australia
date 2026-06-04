"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Play,
  Square,
  Pause,
  Copy,
  Settings,
  Trash2,
  Bot,
  MoreVertical,
  Cpu,
  DollarSign,
  CheckCircle2,
} from "lucide-react";
import type { Agent } from "@/types/agent";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { StatusDot } from "@/components/ui/status-dot";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAgentAction, useDeleteAgent } from "@/hooks/use-agents";
import { formatCurrency, formatPercent, formatRelativeTime, truncate } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { mutate } from "swr";

interface AgentCardProps {
  agent: Agent;
}

const statusBadge = (status: Agent["status"]) => {
  switch (status) {
    case "running": return "success" as const;
    case "paused": return "warning" as const;
    case "error": return "error" as const;
    default: return "muted" as const;
  }
};

export function AgentCard({ agent }: AgentCardProps) {
  const [deleteOpen, setDeleteOpen] = useState(false);
  const { trigger: doAction, isMutating: actionLoading } = useAgentAction(agent.id);
  const { trigger: doDelete, isMutating: deleteLoading } = useDeleteAgent(agent.id);

  const handleAction = async (action: "start" | "stop" | "pause") => {
    try {
      await doAction(action);
      await mutate("/agents");
      toast.success(`Agent ${action}ed`);
    } catch {
      toast.error(`Failed to ${action} agent`);
    }
  };

  const handleDelete = async () => {
    try {
      await doDelete();
      await mutate("/agents");
      toast.success("Agent deleted");
    } catch {
      toast.error("Failed to delete agent");
    }
  };

  return (
    <>
      <div
        className={cn(
          "flex flex-col rounded-lg border bg-cortex-surface p-4 transition-all duration-150",
          agent.status === "running"
            ? "border-cortex-success/30 hover:border-cortex-success/50"
            : agent.status === "error"
            ? "border-cortex-error/30 hover:border-cortex-error/50"
            : "border-cortex-border hover:border-cortex-accent/30"
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="relative flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-cortex-border">
              <Bot className="h-4 w-4 text-cortex-muted" />
              <StatusDot
                status={agent.status}
                size="sm"
                pulse={agent.status === "running"}
                className="absolute -bottom-0.5 -right-0.5"
              />
            </div>
            <div className="min-w-0">
              <Link
                href={`/agents/${agent.id}`}
                className="text-sm font-semibold text-cortex-text hover:text-cortex-accent transition-colors truncate block"
              >
                {agent.name}
              </Link>
              <p className="text-[11px] text-cortex-muted truncate">{truncate(agent.purpose, 50)}</p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
            <Badge variant={statusBadge(agent.status)} className="text-[10px] py-0 px-1.5">
              {agent.status}
            </Badge>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon-sm" aria-label="Agent actions">
                  <MoreVertical className="h-3.5 w-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem asChild>
                  <Link href={`/agents/${agent.id}`}>
                    <Settings className="h-4 w-4" />
                    Configure
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Copy className="h-4 w-4" />
                  Clone
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-cortex-error focus:text-cortex-error focus:bg-cortex-error/10"
                  onClick={() => setDeleteOpen(true)}
                >
                  <Trash2 className="h-4 w-4" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Current task */}
        {agent.currentTask && (
          <div className="mb-3 rounded-md bg-cortex-border/40 px-2.5 py-1.5">
            <p className="text-[11px] text-cortex-muted mb-0.5 uppercase tracking-wider font-medium">Current task</p>
            <p className="text-xs text-cortex-text truncate">{agent.currentTask}</p>
          </div>
        )}

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="flex flex-col items-center rounded-md bg-cortex-border/30 py-1.5 px-1">
            <CheckCircle2 className="h-3 w-3 text-cortex-success mb-0.5" />
            <span className="text-xs font-mono font-semibold text-cortex-text">
              {formatPercent(agent.metrics.successRate, 0)}
            </span>
            <span className="text-[9px] text-cortex-muted uppercase">Success</span>
          </div>
          <div className="flex flex-col items-center rounded-md bg-cortex-border/30 py-1.5 px-1">
            <DollarSign className="h-3 w-3 text-cortex-warning mb-0.5" />
            <span className="text-xs font-mono font-semibold text-cortex-text">
              {formatCurrency(agent.metrics.totalCostUsd, "USD", true)}
            </span>
            <span className="text-[9px] text-cortex-muted uppercase">Cost</span>
          </div>
          <div className="flex flex-col items-center rounded-md bg-cortex-border/30 py-1.5 px-1">
            <Cpu className="h-3 w-3 text-cortex-accent mb-0.5" />
            <span className="text-xs font-mono font-semibold text-cortex-text">
              {agent.metrics.completedTasks}
            </span>
            <span className="text-[9px] text-cortex-muted uppercase">Tasks</span>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between mt-auto pt-2 border-t border-cortex-border">
          <span className="text-[11px] text-cortex-muted">
            {agent.metrics.lastRunAt
              ? formatRelativeTime(agent.metrics.lastRunAt)
              : "Never run"}
          </span>

          {/* Action buttons */}
          <div className="flex items-center gap-1">
            {agent.status === "idle" || agent.status === "stopped" || agent.status === "error" ? (
              <Button
                size="icon-sm"
                variant="ghost"
                aria-label="Start agent"
                onClick={() => handleAction("start")}
                disabled={actionLoading}
                className="hover:text-cortex-success hover:bg-cortex-success/10"
              >
                <Play className="h-3.5 w-3.5" />
              </Button>
            ) : null}

            {agent.status === "running" && (
              <>
                <Button
                  size="icon-sm"
                  variant="ghost"
                  aria-label="Pause agent"
                  onClick={() => handleAction("pause")}
                  disabled={actionLoading}
                  className="hover:text-cortex-warning hover:bg-cortex-warning/10"
                >
                  <Pause className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="icon-sm"
                  variant="ghost"
                  aria-label="Stop agent"
                  onClick={() => handleAction("stop")}
                  disabled={actionLoading}
                  className="hover:text-cortex-error hover:bg-cortex-error/10"
                >
                  <Square className="h-3.5 w-3.5" />
                </Button>
              </>
            )}

            {agent.status === "paused" && (
              <>
                <Button
                  size="icon-sm"
                  variant="ghost"
                  aria-label="Resume agent"
                  onClick={() => handleAction("start")}
                  disabled={actionLoading}
                  className="hover:text-cortex-success hover:bg-cortex-success/10"
                >
                  <Play className="h-3.5 w-3.5" />
                </Button>
                <Button
                  size="icon-sm"
                  variant="ghost"
                  aria-label="Stop agent"
                  onClick={() => handleAction("stop")}
                  disabled={actionLoading}
                  className="hover:text-cortex-error hover:bg-cortex-error/10"
                >
                  <Square className="h-3.5 w-3.5" />
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete Agent"
        description={`Are you sure you want to delete "${agent.name}"? This action cannot be undone. All associated task history and memory will be permanently removed.`}
        confirmLabel="Delete Agent"
        onConfirm={handleDelete}
        isLoading={deleteLoading}
      />
    </>
  );
}
