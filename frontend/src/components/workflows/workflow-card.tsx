"use client";

import Link from "next/link";
import { GitFork, Play, Trash2, MoreVertical, CheckCircle2, XCircle } from "lucide-react";
import type { Workflow } from "@/types/workflow";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useRunWorkflow, useDeleteWorkflow } from "@/hooks/use-workflows";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { mutate } from "swr";

interface WorkflowCardProps {
  workflow: Workflow;
}

const statusVariant = {
  active: "success" as const,
  paused: "warning" as const,
  draft: "muted" as const,
  archived: "muted" as const,
};

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  const { trigger: runWorkflow, isMutating: running } = useRunWorkflow(workflow.id);
  const { trigger: deleteWorkflow, isMutating: deleting } = useDeleteWorkflow(workflow.id);

  const handleRun = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      await runWorkflow();
      toast.success(`Workflow "${workflow.name}" started`);
    } catch {
      toast.error("Failed to start workflow");
    }
  };

  const handleDelete = async () => {
    try {
      await deleteWorkflow();
      await mutate("/workflows");
      toast.success("Workflow deleted");
    } catch {
      toast.error("Failed to delete workflow");
    }
  };

  const nodeCount = workflow.nodes.length;
  const agentNodes = workflow.nodes.filter((n) => n.type === "agent").length;

  return (
    <div className="group rounded-lg border border-cortex-border bg-cortex-surface p-4 hover:border-cortex-accent/30 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cortex-border flex-shrink-0">
            <GitFork className="h-4 w-4 text-cortex-muted" />
          </div>
          <div className="min-w-0">
            <Link
              href={`/workflows/${workflow.id}`}
              className="text-sm font-semibold text-cortex-text hover:text-cortex-accent transition-colors truncate block"
            >
              {workflow.name}
            </Link>
            <p className="text-[11px] text-cortex-muted truncate">{workflow.description || "No description"}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
          <Badge variant={statusVariant[workflow.status]} className="text-[10px] py-0 px-1.5">
            {workflow.status}
          </Badge>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon-sm" aria-label="Workflow actions">
                <MoreVertical className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link href={`/workflows/${workflow.id}`}>Edit Workflow</Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-cortex-error focus:text-cortex-error"
                onClick={handleDelete}
              >
                <Trash2 className="h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Stats */}
      <div className="flex gap-4 mb-3 text-xs text-cortex-muted">
        <span>{nodeCount} nodes</span>
        <span>{agentNodes} agents</span>
        <span>{workflow.runCount} runs</span>
        {workflow.lastRunStatus && (
          <span className={cn(
            "flex items-center gap-1",
            workflow.lastRunStatus === "completed" ? "text-cortex-success" : "text-cortex-error"
          )}>
            {workflow.lastRunStatus === "completed"
              ? <CheckCircle2 className="h-3 w-3" />
              : <XCircle className="h-3 w-3" />}
            Last run
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-cortex-border">
        <span className="text-[11px] text-cortex-muted">
          {workflow.lastRunAt
            ? formatRelativeTime(workflow.lastRunAt)
            : "Never run"}
        </span>
        <div className="flex items-center gap-2">
          <Link
            href={`/workflows/${workflow.id}`}
            className="text-xs text-cortex-accent hover:underline"
          >
            Edit
          </Link>
          {workflow.status === "active" && (
            <Button
              size="sm"
              onClick={handleRun}
              disabled={running}
              className="h-6 px-2 text-xs"
            >
              <Play className="h-3 w-3" />
              {running ? "Running..." : "Run"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
