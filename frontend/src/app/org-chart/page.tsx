"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle, Briefcase, ChevronRight, ChevronsDownUp, ChevronsUpDown, Crown, RefreshCw, Search, User, UserCog, Users2,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AgentDetailSheet } from "@/components/org-chart/agent-detail-sheet";
import { useAgents } from "@/hooks/use-agents";
import { cn } from "@/lib/utils";
import type { Agent } from "@/types/agent";

/** Org chart v2 (2026-10-10, Anthony's audit): real collapsible tree, collapsed by default,
 * "Manager (Venture)" labels with report counts, a visible Consultants tier, and an agent
 * detail drawer on click. */

function StatusDot({ status }: { status: Agent["status"] }) {
  return (
    <span
      className={cn(
        "h-2 w-2 rounded-full flex-none",
        status === "running" ? "bg-cortex-success" : status === "error" ? "bg-destructive" : "bg-muted-foreground/40"
      )}
    />
  );
}

function Branch({ children }: { children: React.ReactNode }) {
  return <div className="flex flex-col gap-1.5 border-l-2 border-border pl-4 ml-[9px]">{children}</div>;
}

function Leaf({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative pl-4 before:absolute before:left-0 before:top-[18px] before:h-px before:w-4 before:bg-border before:content-['']">
      {children}
    </div>
  );
}

function AgentChip({ agent, icon: Icon, onOpen, sub }: { agent: Agent; icon: React.ElementType; onOpen: (a: Agent) => void; sub?: string }) {
  return (
    <button
      type="button"
      onClick={() => onOpen(agent)}
      className="flex items-center gap-2 rounded-md border border-border bg-card px-3 py-1.5 text-sm text-left hover:border-cortex-accent/50 hover:bg-cortex-accent/5 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-cortex-accent"
    >
      <StatusDot status={agent.status} />
      <Icon className="h-3.5 w-3.5 text-muted-foreground flex-none" />
      <span className="font-medium">{agent.name}</span>
      {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
    </button>
  );
}

function Group({
  title, count, icon: Icon, open, onToggle, tone, children, onOpenHead,
}: {
  title: React.ReactNode; count: number; icon: React.ElementType; open: boolean; onToggle: () => void;
  tone: string; children?: React.ReactNode; onOpenHead?: () => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className={cn("flex items-center w-fit rounded-md border", tone)}>
        <button
          type="button"
          onClick={onToggle}
          aria-expanded={open}
          className="flex items-center gap-1 px-2 py-1.5 text-sm hover:bg-white/5 rounded-l-md"
          disabled={count === 0}
          aria-label={open ? "Collapse" : "Expand"}
        >
          <ChevronRight className={cn("h-4 w-4 transition-transform", open && "rotate-90", count === 0 && "opacity-20")} />
        </button>
        <button
          type="button"
          onClick={onOpenHead ?? onToggle}
          className="flex items-center gap-2 pr-3 py-1.5 text-sm text-left hover:underline"
        >
          <Icon className="h-4 w-4 flex-none" />
          <span className="font-semibold">{title}</span>
          <span className="rounded-full bg-muted px-1.5 text-[11px] text-muted-foreground tabular-nums">{count}</span>
        </button>
      </div>
      {open && count > 0 && <Branch>{children}</Branch>}
    </div>
  );
}

export default function OrgChartPage() {
  const { data, error, isLoading, mutate } = useAgents({ pageSize: 500 });
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const agents = useMemo(() => data?.agents ?? [], [data]);
  const byTier = useMemo(() => {
    const g: Record<string, Agent[]> = { consultant: [], manager: [], worker: [] };
    for (const a of agents) (g[a.roleTier] ?? g.worker).push(a);
    for (const k of Object.keys(g)) g[k].sort((a, b) => a.name.localeCompare(b.name));
    return g;
  }, [agents]);

  const reports = useMemo(() => {
    const m = new Map<string, Agent[]>();
    for (const w of byTier.worker) {
      if (!w.reportingManagerId) continue;
      m.set(w.reportingManagerId, [...(m.get(w.reportingManagerId) ?? []), w]);
    }
    return m;
  }, [byTier.worker]);
  const shared = byTier.worker.filter((w) => !w.reportingManagerId);

  const q = query.trim().toLowerCase();
  const matches = (a: Agent) => !q || a.name.toLowerCase().includes(q) || (a.venture ?? "").toLowerCase().includes(q);
  const managers = byTier.manager
    .filter((m) => matches(m) || (reports.get(m.id) ?? []).some(matches))
    .sort((a, b) => (a.venture ?? a.name).localeCompare(b.venture ?? b.name));

  const isOpen = (id: string) => open.has(id) || (!!q && id !== "shared");
  const toggle = (id: string) =>
    setOpen((s) => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  const expandAll = () => setOpen(new Set(["consultants", ...byTier.manager.map((m) => m.id), "shared"]));
  const collapseAll = () => setOpen(new Set());
  const openAgent = (a: Agent) => setSelected(a.id);

  if (error) {
    return (
      <AppShell>
        <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
          <AlertTriangle className="h-10 w-10 text-destructive" />
          <h2 className="text-lg font-semibold">Couldn&apos;t load the chain of command</h2>
          <Button onClick={() => mutate()} variant="outline" size="sm">
            <RefreshCw className="h-3.5 w-3.5 mr-2" /> Retry
          </Button>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex flex-col gap-5 p-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Chain of Command</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Click a manager&apos;s arrow to see their team. Click any name for full details.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                id="org-search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Find an agent or venture"
                className="pl-8 h-8 w-56 text-xs"
              />
            </div>
            <Button variant="outline" size="sm" onClick={expandAll}>
              <ChevronsUpDown className="h-3.5 w-3.5 mr-1" /> Expand all
            </Button>
            <Button variant="outline" size="sm" onClick={collapseAll}>
              <ChevronsDownUp className="h-3.5 w-3.5 mr-1" /> Collapse all
            </Button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="h-10 w-48" />
            <Skeleton className="h-64 w-full" />
          </div>
        ) : (
          <div className="flex flex-col gap-1.5 text-sm">
            <div className="flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 w-fit">
              <Crown className="h-4 w-4 text-amber-500" />
              <span className="font-semibold">Anthony</span>
              <span className="text-xs text-muted-foreground">Owner</span>
            </div>
            <Branch>
              <Leaf>
                <div className="flex items-center gap-2 rounded-md border border-cortex-primary/30 bg-cortex-primary/10 px-3 py-1.5 w-fit">
                  <UserCog className="h-4 w-4 text-cortex-primary" />
                  <span className="font-semibold">Idea Lobster</span>
                  <span className="text-xs text-muted-foreground">Second-in-Command</span>
                </div>
              </Leaf>
              <Branch>
                <Leaf>
                  <Group
                    title="Specialist Consultants"
                    count={byTier.consultant.filter(matches).length}
                    icon={Briefcase}
                    open={isOpen("consultants")}
                    onToggle={() => toggle("consultants")}
                    tone="border-violet-500/40 bg-violet-500/10 text-violet-300"
                  >
                    {byTier.consultant.filter(matches).map((c) => (
                      <Leaf key={c.id}>
                        <AgentChip agent={c} icon={Briefcase} onOpen={openAgent} sub="empire-wide" />
                      </Leaf>
                    ))}
                  </Group>
                </Leaf>

                {managers.map((m) => {
                  const team = (reports.get(m.id) ?? []).filter((w) => matches(w) || matches(m));
                  return (
                    <Leaf key={m.id}>
                      <Group
                        title={
                          <>
                            {m.name} <span className="font-normal text-muted-foreground">({m.venture ?? "no venture"})</span>
                          </>
                        }
                        count={team.length}
                        icon={Users2}
                        open={isOpen(m.id)}
                        onToggle={() => toggle(m.id)}
                        onOpenHead={() => openAgent(m)}
                        tone="border-cortex-success/30 bg-cortex-success/5"
                      >
                        {team.map((w) => (
                          <Leaf key={w.id}>
                            <AgentChip agent={w} icon={User} onOpen={openAgent} />
                          </Leaf>
                        ))}
                      </Group>
                    </Leaf>
                  );
                })}

                <Leaf>
                  <Group
                    title="Shared specialists (no single venture)"
                    count={shared.filter(matches).length}
                    icon={User}
                    open={open.has("shared")}
                    onToggle={() => toggle("shared")}
                    tone="border-border bg-muted/30"
                  >
                    {shared.filter(matches).map((w) => (
                      <Leaf key={w.id}>
                        <AgentChip agent={w} icon={User} onOpen={openAgent} />
                      </Leaf>
                    ))}
                  </Group>
                </Leaf>
              </Branch>
            </Branch>

            <div className="mt-4 flex flex-wrap gap-3 text-xs text-muted-foreground border-t border-border pt-3 tabular-nums">
              <span>{byTier.consultant.length} consultants</span>
              <span>·</span>
              <span>{byTier.manager.length} managers</span>
              <span>·</span>
              <span>{byTier.worker.length - shared.length} workers in venture teams</span>
              <span>·</span>
              <span>{shared.length} shared specialists</span>
            </div>
          </div>
        )}
      </div>
      <AgentDetailSheet agentId={selected} onClose={() => setSelected(null)} />
    </AppShell>
  );
}
