"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Bot,
  ListTodo,
  GitFork,
  Brain,
  Network,
  Package,
  Megaphone,
  DollarSign,
  ScrollText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Zap,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useSystemStore } from "@/store/system-store";
import { useAgentsStore } from "@/store/agents-store";
import { StatusDot } from "@/components/ui/status-dot";

const navItems = [
  {
    group: "Core",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { label: "Agents", href: "/agents", icon: Bot },
      { label: "Tasks", href: "/tasks", icon: ListTodo },
      { label: "Workflows", href: "/workflows", icon: GitFork },
    ],
  },
  {
    group: "Intelligence",
    items: [
      { label: "Memory", href: "/memory", icon: Brain },
      { label: "Knowledge Graph", href: "/knowledge-graph", icon: Network },
    ],
  },
  {
    group: "Ventures",
    items: [
      { label: "Products", href: "/products", icon: Package },
      { label: "Marketing", href: "/marketing", icon: Megaphone },
      { label: "Finance", href: "/finance", icon: DollarSign },
    ],
  },
  {
    group: "System",
    items: [
      { label: "Logs", href: "/logs", icon: ScrollText },
      { label: "Settings", href: "/settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useSystemStore();
  const { getActiveCount } = useAgentsStore();
  const activeAgents = getActiveCount();

  return (
    <aside
      className={cn(
        "flex flex-col bg-cortex-surface border-r border-cortex-border transition-all duration-200 relative flex-shrink-0",
        sidebarCollapsed ? "w-14" : "w-56"
      )}
    >
      {/* Logo */}
      <div className={cn(
        "flex items-center gap-3 px-3 py-4 border-b border-cortex-border",
        sidebarCollapsed && "justify-center px-0"
      )}>
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-cortex-accent flex-shrink-0">
          <Zap className="h-4 w-4 text-white" />
        </div>
        {!sidebarCollapsed && (
          <div className="min-w-0">
            <span className="text-sm font-bold text-cortex-text tracking-tight">CortexOS</span>
            <p className="text-[10px] text-cortex-muted font-mono uppercase tracking-widest">Australia</p>
          </div>
        )}
      </div>

      {/* Active agents badge */}
      {!sidebarCollapsed && activeAgents > 0 && (
        <div className="mx-3 mt-2 mb-1 flex items-center gap-2 rounded-md bg-cortex-success/10 border border-cortex-success/20 px-2.5 py-1.5">
          <Activity className="h-3 w-3 text-cortex-success flex-shrink-0" />
          <span className="text-xs text-cortex-success font-medium">{activeAgents} agent{activeAgents !== 1 ? "s" : ""} running</span>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-2 px-2 space-y-4">
        {navItems.map((group) => (
          <div key={group.group}>
            {!sidebarCollapsed && (
              <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-widest text-cortex-muted">
                {group.group}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.href === "/dashboard"
                    ? pathname === "/dashboard"
                    : pathname.startsWith(item.href);

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      title={sidebarCollapsed ? item.label : undefined}
                      className={cn(
                        "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium transition-colors",
                        sidebarCollapsed && "justify-center px-0",
                        isActive
                          ? "bg-cortex-accent/15 text-cortex-accent"
                          : "text-cortex-muted hover:bg-cortex-border/50 hover:text-cortex-text"
                      )}
                    >
                      <Icon className="h-4 w-4 flex-shrink-0" />
                      {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
                      {!sidebarCollapsed && item.href === "/agents" && activeAgents > 0 && (
                        <StatusDot status="running" size="sm" pulse className="ml-auto" />
                      )}
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={toggleSidebar}
        aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        className={cn(
          "absolute -right-3 top-20 flex h-6 w-6 items-center justify-center rounded-full bg-cortex-surface border border-cortex-border text-cortex-muted hover:text-cortex-text transition-colors z-10",
        )}
      >
        {sidebarCollapsed ? (
          <ChevronRight className="h-3.5 w-3.5" />
        ) : (
          <ChevronLeft className="h-3.5 w-3.5" />
        )}
      </button>
    </aside>
  );
}
