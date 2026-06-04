"use client";

import { useState } from "react";
import {
  Bell,
  Search,
  Wifi,
  WifiOff,
  AlertTriangle,
  LogOut,
  User,
  Settings,
  ChevronDown,
} from "lucide-react";
import { useSystemStore } from "@/store/system-store";
import { useAuthStore } from "@/store/auth-store";
import { useAgentsStore } from "@/store/agents-store";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import Link from "next/link";

export function TopBar() {
  const { health, alerts, dismissAlert } = useSystemStore();
  const { user, logout } = useAuthStore();
  const { wsConnected } = useAgentsStore();
  const [showAlerts, setShowAlerts] = useState(false);

  const undismissedAlerts = alerts.filter((a) => !a.dismissed);
  const errorAlerts = undismissedAlerts.filter((a) => a.level === "error");
  const hasAlerts = undismissedAlerts.length > 0;

  return (
    <header className="flex h-11 items-center gap-3 border-b border-cortex-border bg-cortex-surface px-4 flex-shrink-0">
      {/* Search trigger */}
      <button
        className="flex items-center gap-2 rounded-md border border-cortex-border bg-cortex-bg px-3 py-1.5 text-sm text-cortex-muted hover:border-cortex-accent/40 hover:text-cortex-text transition-colors"
        aria-label="Search (Ctrl+K)"
      >
        <Search className="h-3.5 w-3.5" />
        <span className="hidden sm:block text-xs">Search...</span>
        <kbd className="hidden sm:inline-flex ml-4 h-5 select-none items-center gap-1 rounded border border-cortex-border bg-cortex-surface px-1.5 font-mono text-[10px] font-medium text-cortex-muted">
          ⌘K
        </kbd>
      </button>

      <div className="flex-1" />

      {/* System health */}
      {health && (
        <div className="hidden sm:flex items-center gap-1.5 text-xs">
          <span
            className={cn(
              "font-mono",
              health.overallPercent >= 99 ? "text-cortex-success" :
              health.overallPercent >= 95 ? "text-cortex-warning" :
              "text-cortex-error"
            )}
          >
            {health.overallPercent.toFixed(1)}%
          </span>
          <span className="text-cortex-muted">uptime</span>
          <span className="mx-1 text-cortex-border">·</span>
          <span className="font-mono text-cortex-muted">{health.apiLatencyMs}ms</span>
        </div>
      )}

      {/* WS status */}
      <div
        title={wsConnected ? "Live updates connected" : "Disconnected from live updates"}
        className="flex items-center"
      >
        {wsConnected ? (
          <Wifi className="h-4 w-4 text-cortex-success" />
        ) : (
          <WifiOff className="h-4 w-4 text-cortex-error" />
        )}
      </div>

      {/* Alerts bell */}
      <div className="relative">
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label={`Alerts (${undismissedAlerts.length} unread)`}
          onClick={() => setShowAlerts(!showAlerts)}
          className={cn(hasAlerts && "text-cortex-warning")}
        >
          <Bell className="h-4 w-4" />
          {hasAlerts && (
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-cortex-error text-[9px] font-bold text-white">
              {undismissedAlerts.length > 9 ? "9+" : undismissedAlerts.length}
            </span>
          )}
        </Button>

        {showAlerts && (
          <div className="absolute right-0 top-full mt-2 w-80 z-50 rounded-lg border border-cortex-border bg-cortex-surface shadow-2xl">
            <div className="flex items-center justify-between border-b border-cortex-border px-3 py-2">
              <span className="text-xs font-semibold text-cortex-text">Alerts</span>
              {hasAlerts && (
                <button
                  className="text-xs text-cortex-muted hover:text-cortex-text"
                  onClick={() => {
                    undismissedAlerts.forEach((a) => dismissAlert(a.id));
                    setShowAlerts(false);
                  }}
                >
                  Clear all
                </button>
              )}
            </div>
            <div className="max-h-64 overflow-y-auto">
              {undismissedAlerts.length === 0 ? (
                <p className="py-6 text-center text-xs text-cortex-muted">No alerts</p>
              ) : (
                undismissedAlerts.slice(0, 10).map((alert) => (
                  <div
                    key={alert.id}
                    className="border-b border-cortex-border last:border-0 px-3 py-2 flex gap-2"
                  >
                    <AlertTriangle
                      className={cn(
                        "h-3.5 w-3.5 mt-0.5 flex-shrink-0",
                        alert.level === "error" ? "text-cortex-error" :
                        alert.level === "warning" ? "text-cortex-warning" :
                        alert.level === "success" ? "text-cortex-success" :
                        "text-cortex-accent"
                      )}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-medium text-cortex-text truncate">{alert.title}</p>
                      <p className="text-[11px] text-cortex-muted line-clamp-1">{alert.message}</p>
                    </div>
                    <button
                      onClick={() => dismissAlert(alert.id)}
                      className="text-cortex-muted hover:text-cortex-text text-xs flex-shrink-0"
                      aria-label="Dismiss alert"
                    >
                      ×
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* User menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="gap-2 h-7 px-2">
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-cortex-accent text-[10px] font-bold text-white flex-shrink-0">
              {user?.name?.[0]?.toUpperCase() ?? "U"}
            </div>
            <span className="hidden sm:block text-xs text-cortex-text max-w-[100px] truncate">
              {user?.name ?? "User"}
            </span>
            <ChevronDown className="h-3.5 w-3.5 text-cortex-muted" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuLabel>
            <p className="text-xs font-medium">{user?.name}</p>
            <p className="text-[10px] text-cortex-muted">{user?.email}</p>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem asChild>
            <Link href="/settings">
              <User className="h-4 w-4" />
              Profile
            </Link>
          </DropdownMenuItem>
          <DropdownMenuItem asChild>
            <Link href="/settings">
              <Settings className="h-4 w-4" />
              Settings
            </Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onClick={logout}
            className="text-cortex-error focus:text-cortex-error focus:bg-cortex-error/10"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
