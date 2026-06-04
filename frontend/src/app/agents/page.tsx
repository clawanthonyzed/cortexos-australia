"use client";

import { useState } from "react";
import { Plus, Search, Filter, Bot } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { AgentCard } from "@/components/agents/agent-card";
import { AgentForm } from "@/components/agents/agent-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useAgents } from "@/hooks/use-agents";
import type { AgentStatus } from "@/types/agent";

export default function AgentsPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<AgentStatus | "all">("all");

  const { data, isLoading } = useAgents({
    search: search || undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });

  const agents = data?.agents ?? [];

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Agents</h1>
            <p className="text-sm text-cortex-muted mt-0.5">
              {isLoading ? "Loading..." : `${data?.total ?? 0} agents`}
            </p>
          </div>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            New Agent
          </Button>
        </div>

        {/* Filters */}
        <div className="flex gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cortex-muted" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search agents..."
              className="pl-9"
            />
          </div>
          <Select
            value={statusFilter}
            onValueChange={(v) => setStatusFilter(v as AgentStatus | "all")}
          >
            <SelectTrigger className="w-40">
              <Filter className="h-3.5 w-3.5 mr-1 text-cortex-muted" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="idle">Idle</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="error">Error</SelectItem>
              <SelectItem value="stopped">Stopped</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-cortex-border bg-cortex-surface p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-8 w-8 rounded-lg" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-3.5 w-24" />
                    <Skeleton className="h-3 w-36" />
                  </div>
                </div>
                <Skeleton className="h-8 w-full" />
                <div className="grid grid-cols-3 gap-2">
                  {Array.from({ length: 3 }).map((_, j) => (
                    <Skeleton key={j} className="h-12" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : agents.length === 0 ? (
          <EmptyState
            icon={Bot}
            title="No agents found"
            description={
              search
                ? `No agents matching "${search}"`
                : "Create your first agent to start automating tasks"
            }
            action={
              !search
                ? { label: "Create Agent", onClick: () => setCreateOpen(true) }
                : undefined
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {agents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        )}
      </div>

      {/* Create dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Create Agent</DialogTitle>
          </DialogHeader>
          <AgentForm
            onSuccess={() => setCreateOpen(false)}
            onCancel={() => setCreateOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
