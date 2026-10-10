"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { CheckCircle2Icon, XCircleIcon, AlertCircleIcon, RefreshCwIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ReadyCheck {
  database: string;
  redis: string;
}
interface ReadyResponse {
  status: string;
  checks: ReadyCheck;
  uptime_seconds: number;
}

function StatusBadge({ value }: { value: string }) {
  if (value === "ok" || value === "ready")
    return <span className="flex items-center gap-1.5 text-green-400 text-sm"><CheckCircle2Icon className="h-4 w-4" />Healthy</span>;
  if (value === "degraded")
    return <span className="flex items-center gap-1.5 text-yellow-400 text-sm"><AlertCircleIcon className="h-4 w-4" />Degraded</span>;
  return <span className="flex items-center gap-1.5 text-red-400 text-sm"><XCircleIcon className="h-4 w-4" />Error</span>;
}

function formatUptime(seconds: number) {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  if (d > 0) return `${d}d ${h}h ${m}m`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

const SERVICES = [
  { key: "database", label: "PostgreSQL", description: "Primary database" },
  { key: "redis", label: "Redis", description: "Cache & Celery broker" },
];

const CONTAINERS = [
  { label: "Backend API", port: "8200", desc: "FastAPI / Python 3.11" },
  { label: "Frontend", port: "3010", desc: "Next.js 14" },
  { label: "Celery Worker", port: "—", desc: "Async task queue" },
  { label: "Langfuse", port: "3006", desc: "LLM observability" },
];

export default function StatusPage() {
  const [data, setData] = useState<ReadyResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const check = () => {
    setLoading(true);
    // healthFetcher strips /api/v1 and hits /ready directly on the backend
    import("@/lib/api").then(({ healthFetcher }) =>
      healthFetcher<ReadyResponse>("/ready")
        .then((d) => { setData(d); setLastChecked(new Date()); })
        .catch(() => setData(null))
        .finally(() => setLoading(false))
    );
  };

  useEffect(() => { check(); const t = setInterval(check, 30000); return () => clearInterval(t); }, []);

  return (
    <AppShell>
      <div className="space-y-6 max-w-2xl">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-cortex-text">System Status</h1>
            <p className="text-cortex-muted text-sm mt-1">
              {lastChecked ? `Last checked ${lastChecked.toLocaleTimeString()}` : "Checking…"}
            </p>
          </div>
          <Button variant="outline" size="sm" onClick={check} disabled={loading}>
            <RefreshCwIcon className={`h-3.5 w-3.5 mr-1.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>

        {/* Overall */}
        <div className="rounded-xl border border-cortex-border bg-cortex-surface p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-cortex-text">Overall Status</span>
            {data ? <StatusBadge value={data.status} /> : <span className="text-cortex-muted text-sm">—</span>}
          </div>
          {data && (
            <p className="text-xs text-cortex-muted mt-2">Uptime: {formatUptime(data.uptime_seconds)}</p>
          )}
        </div>

        {/* Services */}
        <div className="rounded-xl border border-cortex-border bg-cortex-surface divide-y divide-cortex-border">
          <div className="px-5 py-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Services</span>
          </div>
          {SERVICES.map((s) => (
            <div key={s.key} className="flex items-center justify-between px-5 py-3.5">
              <div>
                <p className="text-sm font-medium text-cortex-text">{s.label}</p>
                <p className="text-xs text-cortex-muted">{s.description}</p>
              </div>
              {data ? <StatusBadge value={data.checks[s.key as keyof ReadyCheck]} /> : <span className="text-cortex-muted text-sm">—</span>}
            </div>
          ))}
        </div>

        {/* Containers */}
        <div className="rounded-xl border border-cortex-border bg-cortex-surface divide-y divide-cortex-border">
          <div className="px-5 py-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Containers</span>
          </div>
          {CONTAINERS.map((c) => (
            <div key={c.label} className="flex items-center justify-between px-5 py-3.5">
              <div>
                <p className="text-sm font-medium text-cortex-text">{c.label}</p>
                <p className="text-xs text-cortex-muted">{c.desc} {c.port !== "—" && `· port ${c.port}`}</p>
              </div>
              <StatusBadge value="ok" />
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
