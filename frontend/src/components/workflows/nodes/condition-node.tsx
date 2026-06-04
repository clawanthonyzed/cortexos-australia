"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { GitBranch } from "lucide-react";
import type { WorkflowNodeData } from "@/types/workflow";
import { cn } from "@/lib/utils";

export const ConditionNode = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  return (
    <div
      className={cn(
        "min-w-[140px] rounded-lg border-2 bg-cortex-surface px-3 py-2.5 shadow-lg transition-all",
        selected
          ? "border-cortex-warning shadow-[0_0_20px_rgba(245,158,11,0.25)]"
          : "border-cortex-warning/40 hover:border-cortex-warning/70"
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!border-cortex-warning/50 !bg-cortex-bg !w-3 !h-3"
      />

      <div className="flex items-center gap-2 mb-1">
        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-cortex-warning/15 flex-shrink-0">
          <GitBranch className="h-3.5 w-3.5 text-cortex-warning" />
        </div>
        <p className="text-xs font-semibold text-cortex-text truncate">{data.label}</p>
      </div>

      {data.conditions && data.conditions.length > 0 && (
        <div className="mt-1 space-y-0.5">
          {data.conditions.slice(0, 2).map((cond) => (
            <p key={cond.id} className="text-[10px] text-cortex-muted font-mono">
              {cond.field} {cond.operator} {cond.value}
            </p>
          ))}
        </div>
      )}

      {/* True / False handles */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        style={{ left: "30%" }}
        className="!border-cortex-success/50 !bg-cortex-bg !w-3 !h-3"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        style={{ left: "70%" }}
        className="!border-cortex-error/50 !bg-cortex-bg !w-3 !h-3"
      />

      <div className="flex justify-between px-1 mt-0.5">
        <span className="text-[9px] text-cortex-success font-mono">TRUE</span>
        <span className="text-[9px] text-cortex-error font-mono">FALSE</span>
      </div>
    </div>
  );
});

ConditionNode.displayName = "ConditionNode";
