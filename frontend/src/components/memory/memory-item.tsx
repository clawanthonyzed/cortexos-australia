"use client";

import { useState } from "react";
import { ChevronRight, Clock, Tag } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";

/** Matches the actual backend MemoryItemRead schema */
export interface MemoryItemBackend {
  id: string;
  content: string;
  summary: string | null;
  memory_type: string;
  category: string | null;
  tags: string[];
  importance_score: number;
  access_count: number;
  agent_id: string | null;
  user_id: string | null;
  external_id: string | null;
  created_at: string;
  updated_at: string;
}

interface MemoryItemProps {
  item: MemoryItemBackend;
}

const typeVariant: Record<string, "accent" | "success" | "warning" | "muted"> = {
  episodic: "accent",
  semantic: "success",
  procedural: "warning",
  working: "muted",
};

function importanceColor(score: number): string {
  if (score >= 0.8) return "text-cortex-success";
  if (score >= 0.5) return "text-cortex-warning";
  return "text-cortex-muted";
}

export function MemoryItem({ item }: MemoryItemProps) {
  const [expanded, setExpanded] = useState(false);
  const variant = typeVariant[item.memory_type] ?? "muted";
  const excerpt = item.content.length > 120 ? item.content.slice(0, 120) + "..." : item.content;

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
          {item.summary && (
            <p className="text-sm font-semibold text-cortex-text truncate mb-0.5">{item.summary}</p>
          )}
          <p className="text-xs text-cortex-muted truncate">{excerpt}</p>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            <Badge variant={variant} className="text-[9px] py-0 px-1 flex-shrink-0">
              {item.memory_type}
            </Badge>
            {item.category && (
              <Badge variant="muted" className="text-[9px] py-0 px-1 flex-shrink-0">
                {item.category}
              </Badge>
            )}
            <span className={cn("text-[10px] font-mono font-semibold flex-shrink-0", importanceColor(item.importance_score))}>
              {(item.importance_score * 100).toFixed(0)}%
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0 text-[11px] text-cortex-muted">
          <Clock className="h-3 w-3" />
          <span>{formatRelativeTime(item.updated_at)}</span>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-cortex-border px-3 py-3 bg-cortex-bg/30">
          <pre className="text-xs text-cortex-text font-mono whitespace-pre-wrap break-all">{item.content}</pre>

          {item.tags.length > 0 && (
            <div className="mt-2 flex items-center gap-1.5 flex-wrap">
              <Tag className="h-3 w-3 text-cortex-muted" />
              {item.tags.map((tag) => (
                <Badge key={tag} variant="muted" className="text-[10px] py-0 px-1.5">{tag}</Badge>
              ))}
            </div>
          )}

          <div className="mt-2 flex items-center gap-4 text-[11px] text-cortex-muted">
            <span>Accessed {item.access_count} times</span>
            <span>Score: {(item.importance_score * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
