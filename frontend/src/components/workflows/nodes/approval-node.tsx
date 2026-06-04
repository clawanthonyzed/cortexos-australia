"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { UserCheck } from "lucide-react";
import type { WorkflowNodeData } from "@/types/workflow";
import { cn } from "@/lib/utils";

export const ApprovalNode = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  return (
    <div
      className={cn(
        "min-w-[140px] rounded-lg border-2 bg-cortex-surface px-3 py-2.5 shadow-lg transition-all",
        selected
          ? "border-orange-500 shadow-[0_0_20px_rgba(249,115,22,0.25)]"
          : "border-orange-500/40 hover:border-orange-500/70"
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!border-orange-500/50 !bg-cortex-bg !w-3 !h-3"
      />

      <div className="flex items-center gap-2 mb-1">
        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-orange-500/15 flex-shrink-0">
          <UserCheck className="h-3.5 w-3.5 text-orange-400" />
        </div>
        <p className="text-xs font-semibold text-cortex-text truncate">{data.label}</p>
      </div>

      {data.approvers && data.approvers.length > 0 && (
        <p className="text-[10px] text-cortex-muted">
          Approvers: {data.approvers.join(", ")}
        </p>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!border-orange-500/50 !bg-cortex-bg !w-3 !h-3"
      />
    </div>
  );
});

ApprovalNode.displayName = "ApprovalNode";
