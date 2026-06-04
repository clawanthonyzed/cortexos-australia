"use client";

import useSWR from "swr";
import { Brain, Database, Clock, BarChart3 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { MemorySearch } from "@/components/memory/memory-search";
import { fetcher } from "@/lib/api";
import type { MemoryStats } from "@/types/memory";
import { formatBytes, formatRelativeTime } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function MemoryPage() {
  const { data: stats, isLoading: statsLoading } = useSWR<MemoryStats>(
    "/memory/stats",
    fetcher,
    { refreshInterval: 30000 }
  );

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div>
          <h1 className="page-title">Memory Browser</h1>
          <p className="text-sm text-cortex-muted mt-0.5">
            Search and inspect agent memory across all types
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {statsLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="cortex-card space-y-2">
                <Skeleton className="h-3 w-16" />
                <Skeleton className="h-6 w-20" />
              </div>
            ))
          ) : (
            <>
              <div className="cortex-card">
                <div className="flex items-center gap-2 mb-1">
                  <Database className="h-3.5 w-3.5 text-cortex-accent" />
                  <span className="text-xs text-cortex-muted">Total Entries</span>
                </div>
                <p className="text-xl font-bold font-mono text-cortex-text">
                  {(stats?.totalEntries ?? 0).toLocaleString()}
                </p>
              </div>
              <div className="cortex-card">
                <div className="flex items-center gap-2 mb-1">
                  <BarChart3 className="h-3.5 w-3.5 text-cortex-warning" />
                  <span className="text-xs text-cortex-muted">Total Size</span>
                </div>
                <p className="text-xl font-bold font-mono text-cortex-text">
                  {formatBytes(stats?.totalSizeBytes ?? 0)}
                </p>
              </div>
              <div className="cortex-card">
                <div className="flex items-center gap-2 mb-1">
                  <Brain className="h-3.5 w-3.5 text-cortex-success" />
                  <span className="text-xs text-cortex-muted">Agents with Memory</span>
                </div>
                <p className="text-xl font-bold font-mono text-cortex-text">
                  {stats?.byAgent?.length ?? 0}
                </p>
              </div>
              <div className="cortex-card">
                <div className="flex items-center gap-2 mb-1">
                  <Clock className="h-3.5 w-3.5 text-cortex-muted" />
                  <span className="text-xs text-cortex-muted">Last Updated</span>
                </div>
                <p className="text-sm font-medium text-cortex-text">
                  {formatRelativeTime(stats?.newestEntryAt ?? null)}
                </p>
              </div>
            </>
          )}
        </div>

        {/* Type breakdown */}
        {stats?.byType && (
          <div className="cortex-card">
            <p className="text-xs font-semibold uppercase tracking-widest text-cortex-muted mb-3">By Type</p>
            <div className="grid grid-cols-4 gap-3">
              {Object.entries(stats.byType).map(([type, count]) => (
                <div key={type} className="text-center">
                  <p className="text-lg font-bold font-mono text-cortex-text">{count}</p>
                  <p className="text-xs text-cortex-muted capitalize">{type}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search */}
        <Tabs defaultValue="search">
          <TabsList>
            <TabsTrigger value="search">Search</TabsTrigger>
            <TabsTrigger value="by-agent">By Agent</TabsTrigger>
          </TabsList>

          <TabsContent value="search">
            <MemorySearch />
          </TabsContent>

          <TabsContent value="by-agent">
            {stats?.byAgent && stats.byAgent.length > 0 ? (
              <div className="rounded-lg border border-cortex-border overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-cortex-bg/30 border-b border-cortex-border">
                    <tr>
                      <th className="text-left px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Agent</th>
                      <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Entries</th>
                      <th className="text-right px-4 py-2 text-xs font-semibold uppercase tracking-wider text-cortex-muted">Size</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-cortex-border">
                    {stats.byAgent.map((a) => (
                      <tr key={a.agentId} className="hover:bg-cortex-border/20 transition-colors">
                        <td className="px-4 py-2.5 font-medium text-cortex-text">{a.agentName}</td>
                        <td className="px-4 py-2.5 text-right font-mono text-cortex-muted">{a.count}</td>
                        <td className="px-4 py-2.5 text-right font-mono text-cortex-muted">{formatBytes(a.sizeBytes)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="py-8 text-center text-cortex-muted text-sm">No memory data available</div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  );
}
