"use client";

import { useRef, useEffect } from "react";
import type { AgentLog } from "@/types/agent";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface AgentLogsProps {
  logs: AgentLog[];
  isLoading?: boolean;
  autoScroll?: boolean;
}

const levelColor = {
  debug: "text-cortex-muted",
  info: "text-cortex-text",
  warn: "text-cortex-warning",
  error: "text-cortex-error",
};

const levelLabel = {
  debug: "DBG",
  info: "INF",
  warn: "WRN",
  error: "ERR",
};

export function AgentLogs({ logs, isLoading, autoScroll = true }: AgentLogsProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  if (isLoading) {
    return (
      <div className="space-y-2 p-3 font-mono text-xs">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex gap-3">
            <Skeleton className="h-3 w-32" />
            <Skeleton className="h-3 w-8" />
            <Skeleton className="h-3 flex-1" />
          </div>
        ))}
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-xs text-cortex-muted font-mono">
        No logs yet
      </div>
    );
  }

  return (
    <div className="h-64 overflow-y-auto font-mono text-[11px] leading-5 bg-cortex-bg rounded-md border border-cortex-border p-3 space-y-0.5">
      {logs.map((log) => (
        <div key={log.id} className="flex gap-2 group">
          <span className="flex-shrink-0 text-cortex-muted w-32 truncate">
            {formatDateTime(log.timestamp)}
          </span>
          <span
            className={cn(
              "flex-shrink-0 font-semibold w-7",
              levelColor[log.level]
            )}
          >
            {levelLabel[log.level]}
          </span>
          <span className={cn("break-all", levelColor[log.level])}>
            {log.message}
          </span>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
