"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { apiClient } from "@/lib/api";
import { Building2Icon, UserIcon, TagIcon, SearchIcon } from "lucide-react";

interface Venture {
  id: string;
  slug: string;
  name: string;
  manager_name: string;
  category: string;
  created_at: string;
  updated_at: string;
}

interface VenturesResponse {
  items: Venture[];
  total: number;
}

const STATUS_COLORS: Record<string, string> = {
  content: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  ecommerce: "bg-green-500/10 text-green-400 border-green-500/20",
  saas: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  services: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  media: "bg-pink-500/10 text-pink-400 border-pink-500/20",
  empire: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  other: "bg-gray-500/10 text-gray-400 border-gray-500/20",
};

export default function VenturesPage() {
  const [ventures, setVentures] = useState<Venture[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    apiClient
      .get<VenturesResponse>("/ventures")
      .then((d) => setVentures(d.items))
      .catch(() => setError("Failed to load ventures"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = ventures.filter(
    (v) =>
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.manager_name.toLowerCase().includes(search.toLowerCase()) ||
      v.slug.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-cortex-text">Ventures</h1>
            <p className="text-cortex-muted text-sm mt-1">
              {loading ? "Loading…" : `${ventures.length} ventures in the empire`}
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-sm">
          <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cortex-muted" />
          <input
            type="text"
            placeholder="Search ventures…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-lg bg-cortex-surface border border-cortex-border text-cortex-text text-sm placeholder:text-cortex-muted focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Error */}
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {/* Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-cortex-border bg-cortex-surface p-5 animate-pulse h-28" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((v) => (
              <Link
                key={v.id}
                href={`/ventures/${v.id}`}
                className="rounded-xl border border-cortex-border bg-cortex-surface p-5 flex flex-col gap-3 hover:border-blue-500/40 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 shrink-0">
                      <Building2Icon className="h-4 w-4 text-blue-400" />
                    </div>
                    <span className="font-semibold text-cortex-text text-sm leading-tight">{v.name}</span>
                  </div>
                  <span
                    className={`shrink-0 text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                      STATUS_COLORS[v.category] ?? STATUS_COLORS.other
                    }`}
                  >
                    {v.category}
                  </span>
                </div>

                <div className="flex flex-col gap-1.5 text-xs text-cortex-muted">
                  <span className="flex items-center gap-1.5">
                    <UserIcon className="h-3 w-3 shrink-0" />
                    {v.manager_name === "tbd" ? (
                      <span className="italic opacity-50">Manager TBD</span>
                    ) : (
                      v.manager_name
                    )}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <TagIcon className="h-3 w-3 shrink-0" />
                    {v.slug}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}

        {!loading && filtered.length === 0 && (
          <p className="text-center text-cortex-muted text-sm py-12">No ventures match your search.</p>
        )}
      </div>
    </AppShell>
  );
}
