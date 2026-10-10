"use client";

import { AppShell } from "@/components/layout/app-shell";
import Link from "next/link";
import { BotIcon, WorkflowIcon, BrainIcon, Building2Icon, NetworkIcon, ExternalLinkIcon } from "lucide-react";

const SHORTCUTS = [
  { keys: ["⌘", "K"], action: "Global search" },
  { keys: ["⌘", "/"], action: "Toggle sidebar" },
  { keys: ["G", "D"], action: "Go to Dashboard" },
  { keys: ["G", "A"], action: "Go to Agents" },
  { keys: ["G", "W"], action: "Go to Workflows" },
  { keys: ["Esc"], action: "Close modal / panel" },
];

const SECTIONS = [
  {
    icon: <BotIcon className="h-4 w-4 text-blue-400" />,
    title: "Agents",
    path: "/agents",
    desc: "336 empire agents. View status, run tasks, check logs, configure model settings.",
  },
  {
    icon: <Building2Icon className="h-4 w-4 text-purple-400" />,
    title: "Ventures",
    path: "/ventures",
    desc: "42 active ventures. Click any venture to see its agents, documents, and links.",
  },
  {
    icon: <WorkflowIcon className="h-4 w-4 text-green-400" />,
    title: "Workflows",
    path: "/workflows",
    desc: "6 empire loops — product launch QC, booking automation, daily health checks. Run manually or schedule.",
  },
  {
    icon: <BrainIcon className="h-4 w-4 text-yellow-400" />,
    title: "Memory",
    path: "/memory",
    desc: "930 entries from the second brain + agent observations. Searchable by type, category, agent.",
  },
  {
    icon: <NetworkIcon className="h-4 w-4 text-orange-400" />,
    title: "Knowledge Graph",
    path: "/knowledge-graph",
    desc: "Entity-relationship map of all empire agents, ventures, and their connections.",
  },
];

const EXTERNAL = [
  { label: "Mattermost (Team Chat)", url: "https://dash.anthonyzed.work/chat" },
  { label: "Plane (Project Management)", url: "https://dash.anthonyzed.work/plane" },
  { label: "Langfuse (LLM Observability)", url: "https://dash.anthonyzed.work:3006" },
  { label: "WORKFORCE.md (Agent Roster)", url: "https://github.com/clawanthonyzed/business-idea-dash/blob/master/WORKFORCE.md" },
];

export default function HelpPage() {
  return (
    <AppShell>
      <div className="space-y-8 max-w-2xl">
        <div>
          <h1 className="text-2xl font-bold text-cortex-text">Help</h1>
          <p className="text-cortex-muted text-sm mt-1">EmpireOS — Empire Command Centre</p>
        </div>

        {/* Sections */}
        <div className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">What each section does</h2>
          <div className="rounded-xl border border-cortex-border bg-cortex-surface divide-y divide-cortex-border">
            {SECTIONS.map((s) => (
              <Link key={s.path} href={s.path} className="flex items-start gap-3 px-5 py-4 hover:bg-white/5 transition-colors">
                <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg bg-cortex-bg shrink-0">{s.icon}</div>
                <div>
                  <p className="text-sm font-medium text-cortex-text">{s.title}</p>
                  <p className="text-xs text-cortex-muted mt-0.5">{s.desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Keyboard shortcuts */}
        <div className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Keyboard shortcuts</h2>
          <div className="rounded-xl border border-cortex-border bg-cortex-surface divide-y divide-cortex-border">
            {SHORTCUTS.map((s) => (
              <div key={s.action} className="flex items-center justify-between px-5 py-3">
                <span className="text-sm text-cortex-muted">{s.action}</span>
                <div className="flex items-center gap-1">
                  {s.keys.map((k) => (
                    <kbd key={k} className="rounded border border-cortex-border bg-cortex-bg px-2 py-0.5 text-xs font-mono text-cortex-text">{k}</kbd>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* External links */}
        <div className="space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Empire links</h2>
          <div className="rounded-xl border border-cortex-border bg-cortex-surface divide-y divide-cortex-border">
            {EXTERNAL.map((e) => (
              <a key={e.label} href={e.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center justify-between px-5 py-3.5 hover:bg-white/5 transition-colors">
                <span className="text-sm text-cortex-text">{e.label}</span>
                <ExternalLinkIcon className="h-3.5 w-3.5 text-cortex-muted" />
              </a>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
