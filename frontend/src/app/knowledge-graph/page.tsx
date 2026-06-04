"use client";

import useSWR from "swr";
import { Network, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { GraphCanvas } from "@/components/knowledge-graph/graph-canvas";
import { fetcher } from "@/lib/api";
import type { KnowledgeGraph } from "@/types/memory";
import { Button } from "@/components/ui/button";
import { mutate } from "swr";
import { formatRelativeTime } from "@/lib/utils";

export default function KnowledgeGraphPage() {
  const { data, isLoading } = useSWR<KnowledgeGraph>(
    "/knowledge-graph",
    fetcher,
    { refreshInterval: 60000 }
  );

  return (
    <AppShell>
      <div className="flex flex-col h-[calc(100vh-5.5rem)] space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between flex-shrink-0">
          <div>
            <h1 className="page-title">Knowledge Graph</h1>
            <p className="text-sm text-cortex-muted mt-0.5">
              {data
                ? `${data.stats.nodeCount} nodes · ${data.stats.edgeCount} edges · Updated ${formatRelativeTime(data.stats.lastUpdatedAt)}`
                : "Loading graph..."}
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => mutate("/knowledge-graph")}
            aria-label="Refresh graph"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>

        {/* Graph canvas */}
        <div className="flex-1 rounded-lg border border-cortex-border overflow-hidden min-h-0">
          {isLoading || !data ? (
            <div className="flex h-full items-center justify-center">
              <div className="flex flex-col items-center gap-3">
                <Network className="h-8 w-8 text-cortex-muted animate-pulse" />
                <p className="text-sm text-cortex-muted">Building knowledge graph...</p>
              </div>
            </div>
          ) : (
            <GraphCanvas data={data} />
          )}
        </div>
      </div>
    </AppShell>
  );
}
