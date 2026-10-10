"use client";

import useSWR from "swr";
import { Brain, Building2, FileText, ListChecks, Users2, Wrench } from "lucide-react";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fetcher } from "@/lib/api";

interface AgentProfile {
  id: string;
  name: string;
  role_tier: string;
  purpose: string;
  description: string | null;
  status: string;
  model: string;
  tags: string[];
  permitted_tools: string[];
  permitted_services: string[];
  venture: { name: string; slug: string; manager: string | null; status: string; description: string | null } | null;
  reports_to: string | null;
  direct_reports: string[];
  tasks: { id: string; title: string; status: string; priority: number }[];
  memory_count: number;
  md_file: { path: string; content: string | null };
}

const TIER_LABEL: Record<string, string> = {
  consultant: "Specialist Consultant",
  manager: "Venture Manager",
  worker: "Worker",
  owner: "Owner",
  "2ic": "Second-in-Command",
};

function Section({ icon: Icon, title, children }: { icon: React.ElementType; title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-1.5">
      <h3 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-cortex-muted">
        <Icon className="h-3.5 w-3.5" /> {title}
      </h3>
      {children}
    </section>
  );
}

/** Org-chart agent drawer (2026-10-10): role, venture, tools, tasks, memory and the live .md file. */
export function AgentDetailSheet({ agentId, onClose }: { agentId: string | null; onClose: () => void }) {
  const { data: p, error } = useSWR<AgentProfile>(agentId ? `/agents/${agentId}/profile` : null, fetcher);

  return (
    <Sheet open={!!agentId} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full sm:max-w-xl overflow-y-auto">
        {error ? (
          <p className="text-sm text-cortex-error">Couldn&apos;t load this agent. Close and try again.</p>
        ) : !p ? (
          <div className="space-y-3">
            <Skeleton className="h-6 w-40" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        ) : (
          <div className="flex flex-col gap-5">
            <SheetHeader>
              <SheetTitle className="flex flex-wrap items-center gap-2">
                {p.name}
                <Badge variant="muted">{TIER_LABEL[p.role_tier] ?? p.role_tier}</Badge>
              </SheetTitle>
              <SheetDescription>
                {p.venture ? `${p.venture.name} · ` : ""}reports to {p.reports_to ?? "no one yet"} · {p.status}
              </SheetDescription>
            </SheetHeader>

            <Section icon={Users2} title="Role">
              <p className="text-sm leading-relaxed text-cortex-text">{p.description || p.purpose || "No description on file."}</p>
              {p.direct_reports.length > 0 && (
                <p className="text-xs text-cortex-muted">
                  Manages {p.direct_reports.length}: {p.direct_reports.join(", ")}
                </p>
              )}
            </Section>

            <Section icon={Building2} title="Venture">
              {p.venture ? (
                <div className="space-y-1">
                  <p className="text-sm font-medium text-cortex-text">
                    {p.venture.name} <span className="text-xs font-normal text-cortex-muted">· manager {p.venture.manager ?? "none"} · {p.venture.status}</span>
                  </p>
                  {p.venture.description && <p className="text-sm text-cortex-muted leading-relaxed">{p.venture.description}</p>}
                </div>
              ) : (
                <p className="text-sm text-cortex-muted">Empire-wide (not tied to one venture).</p>
              )}
            </Section>

            <Section icon={Wrench} title="Permitted tools & skills">
              <div className="flex flex-wrap gap-1.5">
                {[...p.permitted_tools, ...p.permitted_services].map((t) => (
                  <Badge key={t} variant="outline" className="text-[11px]">{t}</Badge>
                ))}
                {p.permitted_tools.length + p.permitted_services.length === 0 && (
                  <span className="text-sm text-cortex-muted">None listed.</span>
                )}
              </div>
            </Section>

            <Section icon={ListChecks} title={`Tasks (${p.tasks.length})`}>
              {p.tasks.length ? (
                <ul className="space-y-1">
                  {p.tasks.map((t) => (
                    <li key={t.id} className="flex items-center justify-between gap-2 text-sm">
                      <span className="truncate text-cortex-text">{t.title}</span>
                      <Badge variant="muted" className="capitalize text-[11px] shrink-0">{t.status}</Badge>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-cortex-muted">No tasks assigned.</p>
              )}
            </Section>

            <Section icon={Brain} title="Memory">
              <p className="text-sm text-cortex-text">{p.memory_count} entries in central memory</p>
            </Section>

            <Section icon={FileText} title="System instructions (.md file)">
              <p className="text-[11px] text-cortex-muted font-mono">{p.md_file.path}</p>
              {p.md_file.content ? (
                <pre className="max-h-96 overflow-auto rounded-md border border-cortex-border bg-cortex-bg p-3 text-[11px] leading-relaxed text-cortex-text whitespace-pre-wrap">
                  {p.md_file.content}
                </pre>
              ) : (
                <p className="text-sm text-cortex-muted">No .md file found for this agent.</p>
              )}
            </Section>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
