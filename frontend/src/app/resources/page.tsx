"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import { Search, Wrench, X } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { fetcher } from "@/lib/api";
import { cn, formatRelativeTime } from "@/lib/utils";

interface Resource {
  name: string;
  kind: string;
  category: string;
  description: string;
  users: string;
  status: "Active" | "Free tier" | "Offline" | string;
  location: string;
}
interface Catalog {
  generated_at: string | null;
  total: number;
  counts: Record<string, number>;
  categories: Record<string, number>;
  resources: Resource[];
}

const KIND_EMOJI: Record<string, string> = {
  Skill: "🧩", Tool: "🔧", "MCP server": "🔌", "AI model": "🧠", "AI route": "🛣️", Database: "🗄️",
};

function StatusBadge({ status }: { status: string }) {
  const cls =
    status === "Active" ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
    : status === "Free tier" ? "border-sky-500/40 bg-sky-500/10 text-sky-400"
    : "border-red-500/40 bg-red-500/10 text-red-400";
  return <span className={cn("inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 text-[11px] font-medium", cls)}>{status}</span>;
}

/** Resources tab (2026-10-10): searchable inventory of every holding company resource agents may use. Read-only. */
export default function ResourcesPage() {
  const { data, error, isLoading } = useSWR<Catalog>("/resources", fetcher, { refreshInterval: 300000 });
  const [q, setQ] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [kind, setKind] = useState<string | null>(null);

  const shown = useMemo(() => {
    const f = q.trim().toLowerCase();
    return (data?.resources ?? []).filter((r) =>
      (!category || r.category === category) &&
      (!kind || r.kind === kind) &&
      (!f || `${r.name} ${r.description} ${r.users} ${r.category} ${r.kind}`.toLowerCase().includes(f)));
  }, [data, q, category, kind]);

  return (
    <AppShell>
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="page-title flex items-center gap-2"><Wrench className="h-5 w-5" /> Resources</h1>
            <p className="text-sm text-cortex-muted mt-0.5">
              Every tool, skill, model and database the holding company's agents can use, with no permission needed.
              {data?.generated_at && <> Updated {formatRelativeTime(data.generated_at)}.</>}
            </p>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-cortex-muted" />
            <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search tools, e.g. scraping, video, Theodore"
                   aria-label="Search resources" className="pl-8 h-9 w-80 max-w-full text-sm" />
            {q && (
              <button type="button" aria-label="Clear search" onClick={() => setQ("")}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-cortex-muted hover:text-cortex-text">
                <X className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>

        {/* Kind tiles double as filters */}
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
          {isLoading && Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-16" />)}
          {data && Object.entries(data.counts).map(([k, n]) => (
            <button key={k} type="button" onClick={() => setKind(kind === k ? null : k)} aria-pressed={kind === k}
                    className={cn("rounded-lg border bg-cortex-surface px-3 py-2 text-left transition-colors",
                      kind === k ? "border-cortex-accent" : "border-cortex-border hover:border-cortex-accent/40")}>
              <div className="text-xs text-cortex-muted">{KIND_EMOJI[k] ?? "•"} {k}s</div>
              <div className="text-xl font-semibold tabular-nums">{n}</div>
            </button>
          ))}
        </div>

        {/* Category chips */}
        {data && (
          <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by category">
            <button type="button" onClick={() => setCategory(null)}
                    className={cn("rounded-full border px-3 py-1 text-xs", !category ? "border-cortex-accent bg-cortex-accent/10" : "border-cortex-border text-cortex-muted")}>
              All ({data.total})
            </button>
            {Object.entries(data.categories).map(([c, n]) => (
              <button key={c} type="button" onClick={() => setCategory(category === c ? null : c)}
                      className={cn("rounded-full border px-3 py-1 text-xs", category === c ? "border-cortex-accent bg-cortex-accent/10" : "border-cortex-border text-cortex-muted")}>
                {c} ({n})
              </button>
            ))}
          </div>
        )}

        {error && <p className="text-sm text-cortex-error">Couldn't load the resources catalog. Try refreshing.</p>}

        <p className="text-xs text-cortex-muted">{data ? `${shown.length} of ${data.total} shown` : ""}</p>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {isLoading && Array.from({ length: 9 }).map((_, i) => <Skeleton key={i} className="h-36" />)}
          {shown.map((r) => (
            <div key={`${r.kind}:${r.name}`} className="flex min-w-0 flex-col gap-2 rounded-lg border border-cortex-border bg-cortex-surface p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="truncate font-medium text-cortex-text" title={r.name}>{KIND_EMOJI[r.kind] ?? "•"} {r.name}</div>
                  <div className="text-[11px] text-cortex-muted">{r.kind} · {r.category}</div>
                </div>
                <StatusBadge status={r.status} />
              </div>
              <p className="text-sm leading-snug text-cortex-text/90 line-clamp-3">{r.description}</p>
              <div className="mt-auto flex flex-wrap items-center gap-1.5 text-[11px] text-cortex-muted">
                <span>Used by:</span>
                <Badge variant="muted" className="max-w-full truncate">{r.users}</Badge>
              </div>
            </div>
          ))}
        </div>
        {data && shown.length === 0 && (
          <p className="py-10 text-center text-sm text-cortex-muted">No resources match. Clear the search or filters.</p>
        )}
      </div>
    </AppShell>
  );
}
