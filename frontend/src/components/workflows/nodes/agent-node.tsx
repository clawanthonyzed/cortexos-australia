"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { Bot } from "lucide-react";
import type { WorkflowNodeData } from "@/types/workflow";
import { cn } from "@/lib/utils";

export const AgentNode = memo(({ data, selected }: NodeProps<WorkflowNodeData>) => {
  return (
    <div
      className={cn(
        "min-w-[160px] rounded-lg border-2 bg-cortex-surface px-3 py-2.5 shadow-lg transition-all",
        selected
          ? "border-cortex-accent shadow-[0_0_20px_rgba(99,102,241,0.3)]"
          : "border-cortex-accent/40 hover:border-cortex-accent/70"
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!border-cortex-accent/50 !bg-cortex-bg !w-3 !h-3"
      />

      <div className="flex items-center gap-2 mb-1">
        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-cortex-accent/20 flex-shrink-0">
          <Bot className="h-3.5 w-3.5 text-cortex-accent" />
        </div>
        <div className="min-w-0">
          <p className="text-xs font-semibold text-cortex-text truncate">{data.label}</p>
          {data.agentName && (
            <p className="text-[10px] text-cortex-muted truncate">{data.agentName}</p>
          )}
        </div>
      </div>

      {data.promptTemplate && (
        <div className="mt-1.5 rounded bg-cortex-bg px-2 py-1">
          <p className="text-[10px] text-cortex-muted line-clamp-2 font-mono">
            {data.promptTemplate.slice(0, 80)}
            {data.promptTemplate.length > 80 ? "..." : ""}
          </p>
        </div>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!border-cortex-accent/50 !bg-cortex-bg !w-3 !h-3"
      />
    </div>
  );
});

AgentNode.displayName = "AgentNode";
