"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Bot, Play, Square, Pause, Edit3, Save, Zap,
  Activity, DollarSign, CheckCircle2, Cpu, Clock, Brain
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { AgentLogs } from "@/components/agents/agent-logs";
import { AgentForm } from "@/components/agents/agent-form";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle
} from "@/components/ui/dialog";
import { StatusDot } from "@/components/ui/status-dot";
import { PageLoader } from "@/components/ui/loading-spinner";
import { useAgent, useAgentLogs, useAgentAction } from "@/hooks/use-agents";
import {
  formatCurrency, formatPercent, formatTokens,
  formatRelativeTime, formatDuration
} from "@/lib/utils";
import { toast } from "sonner";
import { mutate } from "swr";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [editOpen, setEditOpen] = useState(false);

  const { data: agent, isLoading } = useAgent(id);
  const { data: logsData, isLoading: logsLoading } = useAgentLogs(id);
  const { trigger: doAction, isMutating: actionLoading } = useAgentAction(id);

  const handleAction = async (action: "start" | "stop" | "pause") => {
    try {
      await doAction(action);
      await mutate(`/agents/${id}`);
      toast.success(`Agent ${action}ed`);
    } catch {
      toast.error(`Failed to ${action} agent`);
    }
  };

  if (isLoading) return <AppShell><PageLoader label="Loading agent..." /></AppShell>;
  if (!agent) return <AppShell><div className="text-cortex-muted text-sm">Agent not found</div></AppShell>;

  return (
    <AppShell>
      <div className="space-y-5 max-w-5xl">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-cortex-muted">
          <Link href="/agents" className="flex items-center gap-1.5 hover:text-cortex-text transition-colors">
            <ArrowLeft className="h-4 w-4" />
            Agents
          </Link>
          <span>/</span>
          <span className="text-cortex-text font-medium">{agent.name}</span>
        </div>

        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-cortex-border">
              <Bot className="h-5 w-5 text-cortex-muted" />
              <StatusDot
                status={agent.status}
                size="sm"
                pulse={agent.status === "running"}
                className="absolute -bottom-0.5 -right-0.5"
              />
            </div>
            <div>
              <h1 className="text-xl font-bold text-cortex-text">{agent.name}</h1>
              <p className="text-sm text-cortex-muted">{agent.purpose}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => router.push(`/agents/${id}/playground`)}>
              <Zap className="h-3.5 w-3.5" />
              Playground
            </Button>
            <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
              <Edit3 className="h-3.5 w-3.5" />
              Edit
            </Button>

            {(agent.status === "idle" || agent.status === "stopped" || agent.status === "error") && (
              <Button size="sm" onClick={() => handleAction("start")} disabled={actionLoading}
                className="bg-cortex-success hover:bg-green-400 text-white">
                <Play className="h-3.5 w-3.5" />
                Start
              </Button>
            )}
            {agent.status === "running" && (
              <>
                <Button variant="outline" size="sm" onClick={() => handleAction("pause")} disabled={actionLoading}>
                  <Pause className="h-3.5 w-3.5" />
                  Pause
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleAction("stop")} disabled={actionLoading}
                  className="border-cortex-error/30 text-cortex-error hover:bg-cortex-error/10">
                  <Square className="h-3.5 w-3.5" />
                  Stop
                </Button>
              </>
            )}
            {agent.status === "paused" && (
              <Button size="sm" onClick={() => handleAction("start")} disabled={actionLoading}
                className="bg-cortex-success hover:bg-green-400 text-white">
                <Play className="h-3.5 w-3.5" />
                Resume
              </Button>
            )}
          </div>
        </div>

        {/* Metrics row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            {
              label: "Success Rate",
              value: formatPercent(agent.metrics.successRate),
              icon: CheckCircle2,
              color: "text-cortex-success"
            },
            {
              label: "Total Cost",
              value: formatCurrency(agent.metrics.totalCostUsd, "USD"),
              icon: DollarSign,
              color: "text-cortex-warning"
            },
            {
              label: "Tokens Used",
              value: formatTokens(agent.metrics.totalTokensUsed),
              icon: Cpu,
              color: "text-cortex-accent"
            },
            {
              label: "Avg Duration",
              value: formatDuration(agent.metrics.averageTaskDurationMs),
              icon: Clock,
              color: "text-cortex-muted"
            },
          ].map((m) => (
            <div key={m.label} className="cortex-card">
              <div className="flex items-center gap-2 mb-1">
                <m.icon className={`h-3.5 w-3.5 ${m.color}`} />
                <span className="text-xs text-cortex-muted">{m.label}</span>
              </div>
              <p className="text-lg font-bold font-mono text-cortex-text">{m.value}</p>
            </div>
          ))}
        </div>

        {/* Current task */}
        {agent.currentTask && (
          <div className="rounded-lg border border-cortex-accent/30 bg-cortex-accent/5 px-4 py-3">
            <p className="text-xs font-medium text-cortex-accent mb-1 uppercase tracking-wider">Running Now</p>
            <p className="text-sm text-cortex-text">{agent.currentTask}</p>
          </div>
        )}

        {/* Tabs */}
        <Tabs defaultValue="logs">
          <TabsList>
            <TabsTrigger value="logs">Execution Logs</TabsTrigger>
            <TabsTrigger value="memory">Memory ({agent.memory.entryCount})</TabsTrigger>
            <TabsTrigger value="config">Configuration</TabsTrigger>
          </TabsList>

          <TabsContent value="logs">
            <AgentLogs
              logs={logsData?.logs ?? []}
              isLoading={logsLoading}
              autoScroll
            />
          </TabsContent>

          <TabsContent value="memory">
            <div className="cortex-card">
              <div className="flex items-center gap-2 mb-3">
                <Brain className="h-4 w-4 text-cortex-accent" />
                <span className="text-sm font-semibold">Agent Memory</span>
              </div>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <p className="text-xl font-bold font-mono text-cortex-text">{agent.memory.entryCount}</p>
                  <p className="text-xs text-cortex-muted">Entries</p>
                </div>
                <div>
                  <p className="text-xl font-bold font-mono text-cortex-text">
                    {(agent.memory.sizeBytes / 1024).toFixed(1)}KB
                  </p>
                  <p className="text-xs text-cortex-muted">Size</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-cortex-text">
                    {formatRelativeTime(agent.memory.lastUpdatedAt)}
                  </p>
                  <p className="text-xs text-cortex-muted">Last updated</p>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="config">
            <div className="cortex-card">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-xs text-cortex-muted mb-1">Model</p>
                  <p className="font-mono text-cortex-text">{agent.model}</p>
                </div>
                <div>
                  <p className="text-xs text-cortex-muted mb-1">Venture</p>
                  <p className="text-cortex-text">{agent.venture ?? "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-cortex-muted mb-1">Slug</p>
                  <p className="font-mono text-cortex-text">{agent.slug}</p>
                </div>
                <div>
                  <p className="text-xs text-cortex-muted mb-1">Created</p>
                  <p className="text-cortex-text">{formatRelativeTime(agent.createdAt)}</p>
                </div>
                {agent.capabilities.length > 0 && (
                  <div className="col-span-2">
                    <p className="text-xs text-cortex-muted mb-2">Capabilities</p>
                    <div className="flex flex-wrap gap-1.5">
                      {agent.capabilities.map((cap) => (
                        <Badge key={cap} variant="accent" className="text-[10px]">{cap}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {agent.tags.length > 0 && (
                  <div className="col-span-2">
                    <p className="text-xs text-cortex-muted mb-2">Tags</p>
                    <div className="flex flex-wrap gap-1.5">
                      {agent.tags.map((tag) => (
                        <Badge key={tag} variant="muted" className="text-[10px]">{tag}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Edit dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Edit Agent</DialogTitle>
          </DialogHeader>
          <AgentForm
            agent={agent}
            onSuccess={() => setEditOpen(false)}
            onCancel={() => setEditOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
