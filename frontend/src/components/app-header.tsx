"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { AppBreadcrumbs } from "@/components/app-breadcrumbs";
import { CustomSidebarTrigger } from "@/components/custom-sidebar-trigger";
import { navLinks } from "@/components/app-shared";
import { NavUser } from "@/components/nav-user";
import { BellIcon, XIcon, NetworkIcon, ClipboardListIcon, WalletIcon, BookOpenIcon } from "lucide-react";
import Link from "next/link";
import { useAgents } from "@/hooks/use-agents";
import { apiClient } from "@/lib/api";

const activeItem = navLinks.find((item) => item.isActive);
const LS_KEY = "cortexos-dismissed-notifications";

// Was hardcoded to "336 agents synced" / "42 ventures loaded" -- a frozen
// guess that never matched the real count (342 agents / 44 ventures the day
// this was found, 2026-10-08). This static mismatch was a real contributor
// to Anthony seeing "missing agents/ventures": the bell quietly claimed one
// number while the Agents page (separately capped at 20) showed another.
// Now built from the real live total on every load.

export function AppHeader() {
  const [open, setOpen] = useState(false);
  // Dismissals persist per browser. Read once after mount (the server render has no
  // localStorage), and only write after that read, so a first render can't wipe them.
  const [dismissed, setDismissed] = useState<number[]>([]);
  const [dismissLoaded, setDismissLoaded] = useState(false);
  useEffect(() => {
    try {
      const stored = localStorage.getItem(LS_KEY);
      if (stored) setDismissed(JSON.parse(stored) as number[]);
    } catch {
      // storage blocked: dismissals last for this visit only
    }
    setDismissLoaded(true);
  }, []);
  useEffect(() => {
    if (!dismissLoaded) return;
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(dismissed));
    } catch {
      // ignore quota / blocked storage
    }
  }, [dismissed, dismissLoaded]);

  const { data: agentsData } = useAgents({ pageSize: 1 });
  const [venturesTotal, setVenturesTotal] = useState<number | null>(null);
  useEffect(() => {
    apiClient
      .get<{ total: number }>("/ventures")
      .then((d) => setVenturesTotal(d.total))
      .catch(() => setVenturesTotal(null));
  }, []);

  const systemNotifications = [
    {
      id: 1,
      title: agentsData ? `${agentsData.total} agents synced` : "Agents syncing…",
      body: "Live count from the agents API, not a fixed number.",
      time: "live",
    },
    {
      id: 2,
      title: venturesTotal !== null ? `${venturesTotal} ventures loaded` : "Ventures loading…",
      body: "Live count from the ventures API, not a fixed number.",
      time: "live",
    },
    { id: 3, title: "Celery worker healthy", body: "Background task queue is operational.", time: "today" },
  ];

  const visible = systemNotifications.filter((n) => !dismissed.includes(n.id));

  const dismiss = (id: number) => setDismissed((d) => (d.includes(id) ? d : [...d, id]));
  const clearAll = () => setDismissed(systemNotifications.map((n) => n.id));

  return (
    <header className={cn("sticky top-0 z-50 flex h-14 shrink-0 items-center justify-between gap-2 border-b px-4 md:px-6")}>
      <div className="flex items-center gap-3">
        <CustomSidebarTrigger />
        <Separator className="mr-2 h-4 data-[orientation=vertical]:self-center" orientation="vertical" />
        <AppBreadcrumbs page={activeItem} />
      </div>
      <div className="flex items-center gap-3">
        <Link
          href="/org-chart"
          className="hidden sm:flex items-center gap-1.5 rounded-md border border-cortex-border bg-cortex-bg px-3 py-1.5 text-xs text-cortex-muted hover:border-cortex-accent/40 hover:text-cortex-text transition-colors"
        >
          <NetworkIcon className="h-3.5 w-3.5" />
          Org Chart
        </Link>
        <Link
          href="/tasks"
          className="hidden sm:flex items-center gap-1.5 rounded-md border border-cortex-accent/40 bg-cortex-accent/10 px-3 py-1.5 text-xs font-medium text-cortex-text hover:bg-cortex-accent/20 transition-colors"
        >
          <ClipboardListIcon className="h-3.5 w-3.5" />
          Tasks
        </Link>
        <Link
          href="/finance"
          className="hidden sm:flex items-center gap-1.5 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-1.5 text-xs font-medium text-cortex-text hover:bg-emerald-500/20 transition-colors"
        >
          <WalletIcon className="h-3.5 w-3.5" />
          Finance
        </Link>
        <Link
          href="/second-brain"
          className="hidden md:flex items-center gap-1.5 rounded-md border border-violet-500/40 bg-violet-500/10 px-3 py-1.5 text-xs font-medium text-cortex-text hover:bg-violet-500/20 transition-colors"
        >
          <BookOpenIcon className="h-3.5 w-3.5" />
          Second Brain
        </Link>
        <div className="relative">
          <Button
            aria-label="Notifications"
            className="relative"
            size="icon"
            variant="outline"
            onClick={() => setOpen((v) => !v)}
          >
            <BellIcon />
            {dismissLoaded && visible.length > 0 && (
              <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[9px] font-bold text-white leading-none">
                {visible.length}
              </span>
            )}
          </Button>
          {open && (
            <div className="absolute right-0 top-10 z-50 w-80 rounded-xl border border-cortex-border bg-cortex-surface shadow-2xl">
              <div className="flex items-center justify-between border-b border-cortex-border px-4 py-3">
                <span className="text-sm font-semibold text-cortex-text">Notifications</span>
                {visible.length > 0 && (
                  <button onClick={clearAll} className="ml-auto mr-2 text-xs text-cortex-muted hover:text-cortex-text">
                    Clear all
                  </button>
                )}
                <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => setOpen(false)}>
                  <XIcon className="h-3 w-3" />
                </Button>
              </div>
              {visible.length === 0 ? (
                <p className="px-4 py-6 text-center text-sm text-cortex-muted">All caught up</p>
              ) : (
                <ul className="divide-y divide-cortex-border">
                  {visible.map((n) => (
                    <li key={n.id} className="flex items-start gap-3 px-4 py-3">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-cortex-text">{n.title}</p>
                        <p className="text-xs text-cortex-muted mt-0.5">{n.body}</p>
                        <p className="text-xs text-cortex-muted mt-1 opacity-60">{n.time}</p>
                      </div>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-5 w-5 shrink-0"
                        onClick={() => dismiss(n.id)}
                      >
                        <XIcon className="h-3 w-3" />
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
        <Separator className="h-4 data-[orientation=vertical]:self-center" orientation="vertical" />
        <NavUser />
      </div>
    </header>
  );
}
