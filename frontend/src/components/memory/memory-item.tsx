"use client";

import { useState } from "react";
import { ChevronRight, Bot, Clock, Tag } from "lucide-react";
import type { MemoryItem } from "@/types/memory";
import { Badge } from "@/components/ui/badge";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface MemoryItemProps {
  item: MemoryItem;
}

const typeVariant = {
  episodic: "accent" as const,
  semantic: "success" as const,
  procedural: "warning" as const,
  working: "muted" as const,
};

export function MemoryItem({ item }: MemoryItemProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className="rounded-lg border border-cortex-border bg-cortex-surface hover:border-cortex-accent/30 transition-colors cursor-pointer"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center gap-3 px-3 py-2.5">
        <ChevronRight
          className={cn(
            "h-4 w-4 text-cortex-muted transition-transform flex-shrink-0",
            expanded && "rotate-90"
          )}
        />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-sm font-mono font-medium text-cortex-text truncate">{item.key}</span>
            <Badge variant={typeVariant[item.type]} className="text-[9px] py-0 px-1 flex-shrink-0">
              {item.type}
            </Badge>
          </div>
          <p className="text-xs text-cortex-muted truncate">
            {typeof item.value === "string" && item.value.length > 100
              ? item.value.slice(0, 100) + "..."
              : item.value}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-shrink-0 text-[11px] text-cortex-muted">
          <div className="hidden sm:flex items-center gap-1">
            <Bot className="h-3 w-3" />
            <span>{item.agentName}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{formatRelativeTime(item.updatedAt)}</span>
          </div>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-cortex-border px-3 py-3 bg-cortex-bg/30">
          <pre className="text-xs text-cortex-text font-mono whitespace-pre-wrap break-all">
            {typeof item.value === "object" ? JSON.stringify(item.value, null, 2) : item.value}
          </pre>

          {item.tags.length > 0 && (
            <div className="mt-2 flex items-center gap-1.5 flex-wrap">
              <Tag className="h-3 w-3 text-cortex-muted" />
              {item.tags.map((tag) => (
                <Badge key={tag} variant="muted" className="text-[10px] py-0 px-1.5">
                  {tag}
                </Badge>
              ))}
            </div>
          )}

          <div className="mt-2 flex items-center gap-4 text-[11px] text-cortex-muted">
            <span>Accessed {item.accessCount} times</span>
            {item.lastAccessedAt && <span>Last: {formatRelativeTime(item.lastAccessedAt)}</span>}
            {item.expiresAt && <span>Expires: {formatRelativeTime(item.expiresAt)}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
