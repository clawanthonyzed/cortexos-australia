"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { apiClient } from "@/lib/api";
import {
  Building2Icon,
  UserIcon,
  TagIcon,
  ArrowLeftIcon,
  BotIcon,
  GithubIcon,
  MessageSquareIcon,
  TrelloIcon,
  DollarSignIcon,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

interface Venture {
  id: string;
  slug: string;
  name: string;
  manager_name: string;
  category: string;
  created_at: string;
  updated_at: string;
}

interface AgentBrief {
  id: string;
  name: string;
  purpose: string;
  status: string;
  tags: string[];
}

interface AgentsResponse {
  items: AgentBrief[];
  total: number;
}

const STATUS_DOT: Record<string, string> = {
  running: "bg-green-400",
  idle: "bg-gray-400",
  error: "bg-red-400",
  paused: "bg-yellow-400",
  stopped: "bg-gray-600",
};

export default function VentureDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [venture, setVenture] = useState<Venture | null>(null);
  const [agents, setAgents] = useState<AgentBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    apiClient.get<Venture>(`/ventures/${id}`)
      .then((v) => {
        setVenture(v);
        return apiClient.get<AgentsResponse>(`/agents?venture=${v.slug}&page_size=50`)
          .then((a) => setAgents(a.items));
      })
      .catch(() => setError("Failed to load venture"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <AppShell>
        <div className="space-y-6 max-w-3xl">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </AppShell>
    );
  }

  if (error || !venture) {
    return (
      <AppShell>
        <div className="space-y-4">
          <Link href="/ventures" className="inline-flex items-center gap-1.5 text-sm text-cortex-muted hover:text-cortex-text">
            <ArrowLeftIcon className="h-3.5 w-3.5" /> Back to Ventures
          </Link>
          <p className="text-red-400">{error || "Venture not found"}</p>
        </div>
      </AppShell>
    );
  }

  const quickLinks = [
    {
      label: "GitHub Repo",
      url: `https://github.com/clawanthonyzed/${venture.slug}`,
      icon: <GithubIcon className="h-4 w-4" />,
    },
    {
      label: "Mattermost Channel",
      url: `https://dash.anthonyzed.work/chat/channels/${venture.slug}`,
      icon: <MessageSquareIcon className="h-4 w-4" />,
    },
    {
      label: "Plane Project",
      url: `https://dash.anthonyzed.work/plane`,
      icon: <TrelloIcon className="h-4 w-4" />,
    },
  ];

  return (
    <AppShell>
      <div className="space-y-6 max-w-3xl">
        {/* Back */}
        <Link href="/ventures" className="inline-flex items-center gap-1.5 text-sm text-cortex-muted hover:text-cortex-text transition-colors">
          <ArrowLeftIcon className="h-3.5 w-3.5" /> Back to Ventures
        </Link>

        {/* Header */}
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 shrink-0">
            <Building2Icon className="h-6 w-6 text-blue-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-cortex-text">{venture.name}</h1>
              <Badge variant="muted" className="text-[11px]">{venture.category}</Badge>
            </div>
            <div className="flex items-center gap-4 mt-1.5 text-sm text-cortex-muted flex-wrap">
              <span className="flex items-center gap-1.5">
                <UserIcon className="h-3.5 w-3.5" />
                {venture.manager_name === "tbd" ? <em>Manager TBD</em> : venture.manager_name}
              </span>
              <span className="flex items-center gap-1.5">
                <TagIcon className="h-3.5 w-3.5" />
                {venture.slug}
              </span>
            </div>
          </div>
        </div>

        {/* Agents */}
        <div className="rounded-xl border border-cortex-border bg-cortex-surface overflow-hidden">
          <div className="px-5 py-3 border-b border-cortex-border flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">
              Agents ({agents.length})
            </span>
            <Link href={`/agents`} className="text-xs text-cortex-accent hover:underline">
              View all agents
            </Link>
          </div>
          {agents.length === 0 ? (
            <p className="px-5 py-6 text-sm text-cortex-muted text-center">No agents tagged to this venture yet.</p>
          ) : (
            <div className="divide-y divide-cortex-border">
              {agents.map((ag) => (
                <Link
                  key={ag.id}
                  href={`/agents/${ag.id}`}
                  className="flex items-center gap-3 px-5 py-3.5 hover:bg-white/5 transition-colors"
                >
                  <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-cortex-bg shrink-0">
                    <BotIcon className="h-3.5 w-3.5 text-cortex-muted" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-cortex-text truncate">{ag.name}</p>
                    <p className="text-xs text-cortex-muted truncate">{ag.purpose}</p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className={`h-2 w-2 rounded-full ${STATUS_DOT[ag.status] ?? "bg-gray-400"}`} />
                    <span className="text-xs text-cortex-muted capitalize">{ag.status}</span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Revenue */}
        <div className="rounded-xl border border-cortex-border bg-cortex-surface p-5">
          <div className="flex items-center gap-2 mb-3">
            <DollarSignIcon className="h-4 w-4 text-cortex-success" />
            <span className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Revenue</span>
          </div>
          <p className="text-sm text-cortex-muted">Revenue data coming soon — connect Gumroad / Etsy / LemonSqueezy to see live figures.</p>
        </div>

        {/* Quick links */}
        <div className="rounded-xl border border-cortex-border bg-cortex-surface divide-y divide-cortex-border">
          <div className="px-5 py-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Quick Links</span>
          </div>
          {quickLinks.map((l) => (
            <a
              key={l.label}
              href={l.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-5 py-3.5 hover:bg-white/5 transition-colors"
            >
              <span className="text-cortex-muted">{l.icon}</span>
              <span className="text-sm text-cortex-text">{l.label}</span>
            </a>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
