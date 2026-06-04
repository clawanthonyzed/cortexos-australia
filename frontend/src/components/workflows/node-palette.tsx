"use client";

import { Bot, GitBranch, UserCheck, Play, Square, Webhook, Clock } from "lucide-react";
import type { NodeType } from "@/types/workflow";

interface PaletteItem {
  type: NodeType;
  label: string;
  description: string;
  icon: React.ElementType;
  color: string;
  bgColor: string;
  borderColor: string;
}

const paletteItems: PaletteItem[] = [
  {
    type: "start",
    label: "Start",
    description: "Workflow entry point",
    icon: Play,
    color: "text-cortex-muted",
    bgColor: "bg-cortex-border",
    borderColor: "border-cortex-muted/30",
  },
  {
    type: "agent",
    label: "Agent",
    description: "Run an AI agent",
    icon: Bot,
    color: "text-cortex-accent",
    bgColor: "bg-cortex-accent/15",
    borderColor: "border-cortex-accent/30",
  },
  {
    type: "condition",
    label: "Condition",
    description: "Branch on logic",
    icon: GitBranch,
    color: "text-cortex-warning",
    bgColor: "bg-cortex-warning/15",
    borderColor: "border-cortex-warning/30",
  },
  {
    type: "approval",
    label: "Approval",
    description: "Require human approval",
    icon: UserCheck,
    color: "text-orange-400",
    bgColor: "bg-orange-500/15",
    borderColor: "border-orange-500/30",
  },
  {
    type: "webhook",
    label: "Webhook",
    description: "HTTP request/callback",
    icon: Webhook,
    color: "text-blue-400",
    bgColor: "bg-blue-500/15",
    borderColor: "border-blue-500/30",
  },
  {
    type: "delay",
    label: "Delay",
    description: "Wait for duration",
    icon: Clock,
    color: "text-purple-400",
    bgColor: "bg-purple-500/15",
    borderColor: "border-purple-500/30",
  },
  {
    type: "end",
    label: "End",
    description: "Workflow exit point",
    icon: Square,
    color: "text-cortex-muted",
    bgColor: "bg-cortex-border",
    borderColor: "border-cortex-muted/30",
  },
];

interface NodePaletteProps {
  onDragStart: (event: React.DragEvent, nodeType: NodeType) => void;
}

export function NodePalette({ onDragStart }: NodePaletteProps) {
  return (
    <div className="p-3 space-y-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-cortex-muted mb-3">
        Node Types
      </p>
      {paletteItems.map((item) => {
        const Icon = item.icon;
        return (
          <div
            key={item.type}
            draggable
            onDragStart={(e) => onDragStart(e, item.type)}
            className={`flex items-center gap-2.5 rounded-md border ${item.borderColor} ${item.bgColor} px-2.5 py-2 cursor-grab active:cursor-grabbing hover:opacity-90 transition-opacity select-none`}
          >
            <Icon className={`h-3.5 w-3.5 flex-shrink-0 ${item.color}`} />
            <div className="min-w-0">
              <p className="text-xs font-medium text-cortex-text">{item.label}</p>
              <p className="text-[10px] text-cortex-muted truncate">{item.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
