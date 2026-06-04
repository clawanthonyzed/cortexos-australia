"use client";

import {
  Bot, DollarSign, ListChecks, Cpu, Activity, TrendingUp
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { StatCard } from "@/components/dashboard/stat-card";
import { RevenueChart } from "@/components/dashboard/revenue-chart";
import { AgentStatusWidget } from "@/components/dashboard/agent-status";
import { TaskQueueWidget } from "@/components/dashboard/task-queue";
import { CostTracker } from "@/components/dashboard/cost-tracker";
import { SystemHealthWidget } from "@/components/dashboard/system-health";
import { useDashboardStats, useFinance } from "@/hooks/use-finance";
import { useAgents } from "@/hooks/use-agents";
import { useTasks } from "@/hooks/use-tasks";
import { useSystemStore } from "@/store/system-store";
import { formatCurrency, formatTokens, formatPercent } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: financeData, isLoading: financeLoading } = useFinance({ period: "30d" });
  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const { data: tasksData, isLoading: tasksLoading } = useTasks({ pageSize: 10 });
  const { health } = useSystemStore();

  return (
    <AppShell>
      <div className="space-y-6">
        {/* Page title */}
        <div>
          <h1 className="page-title">Command Center</h1>
          <p className="text-sm text-cortex-muted mt-0.5">Live system overview</p>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-6">
          <StatCard
            title="Active Agents"
            value={statsLoading ? "—" : String(stats?.activeAgents ?? 0)}
            delta={stats?.activeAgentsDelta}
            deltaLabel="vs yesterday"
            icon={Bot}
            iconColor="accent"
            isLoading={statsLoading}
          />
          <StatCard
            title="Revenue (MTD)"
            value={statsLoading ? "—" : formatCurrency(stats?.revenueThisMonthAud ?? 0, "AUD", true)}
            delta={stats?.revenueGrowthPercent}
            deltaLabel="vs last month"
            icon={DollarSign}
            iconColor="success"
            isLoading={statsLoading}
          />
          <StatCard
            title="Monthly Costs"
            value={statsLoading ? "—" : formatCurrency(stats?.costsThisMonthUsd ?? 0, "USD", true)}
            delta={stats?.costsGrowthPercent}
            deltaLabel="vs last month"
            icon={TrendingUp}
            iconColor="warning"
            trend={stats ? (stats.costsGrowthPercent > 0 ? "down" : "up") : undefined}
            isLoading={statsLoading}
          />
          <StatCard
            title="Tasks Today"
            value={statsLoading ? "—" : String(stats?.tasksCompletedToday ?? 0)}
            delta={stats?.tasksCompletedDelta}
            deltaLabel="vs yesterday"
            icon={ListChecks}
            iconColor="success"
            isLoading={statsLoading}
          />
          <StatCard
            title="Token Usage"
            value={statsLoading ? "—" : `${formatTokens((stats?.tokenUsageTodayM ?? 0) * 1_000_000)}`}
            delta={stats?.tokenUsageDeltaPercent}
            deltaLabel="vs yesterday"
            icon={Cpu}
            iconColor="accent"
            isLoading={statsLoading}
          />
          <StatCard
            title="System Health"
            value={statsLoading ? "—" : formatPercent(stats?.systemHealthPercent ?? 100, 1)}
            icon={Activity}
            iconColor={
              (stats?.systemHealthPercent ?? 100) >= 99
                ? "success"
                : (stats?.systemHealthPercent ?? 100) >= 95
                ? "warning"
                : "error"
            }
            subtitle="uptime"
            isLoading={statsLoading}
          />
        </div>

        {/* Main 2-col layout */}
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          {/* Left col: Revenue chart + Task queue */}
          <div className="xl:col-span-2 space-y-4">
            {/* Revenue chart */}
            <div className="cortex-card">
              <div className="section-header">
                <div>
                  <h2 className="text-sm font-semibold text-cortex-text">Revenue vs Costs</h2>
                  <p className="text-xs text-cortex-muted">Last 30 days</p>
                </div>
                <div className="flex items-center gap-3 text-xs text-cortex-muted">
                  <span className="flex items-center gap-1.5">
                    <span className="h-2.5 w-4 rounded-sm bg-cortex-accent/70 inline-block" />
                    Revenue
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-2.5 w-4 rounded-sm bg-cortex-warning/70 inline-block" style={{ backgroundImage: "repeating-linear-gradient(45deg, transparent, transparent 1px, rgba(245,158,11,0.5) 1px, rgba(245,158,11,0.5) 2px)" }} />
                    Costs
                  </span>
                </div>
              </div>
              <RevenueChart
                data={financeData?.revenueHistory ?? []}
                isLoading={financeLoading}
              />
            </div>

            {/* Task queue */}
            <div className="cortex-card">
              <div className="section-header">
                <div>
                  <h2 className="text-sm font-semibold text-cortex-text">Recent Tasks</h2>
                  <p className="text-xs text-cortex-muted">Last 10 tasks</p>
                </div>
                <a href="/tasks" className="text-xs text-cortex-accent hover:underline">View all</a>
              </div>
              <TaskQueueWidget
                tasks={tasksData?.tasks ?? []}
                isLoading={tasksLoading}
              />
            </div>
          </div>

          {/* Right col: Agents + Cost + Health */}
          <div className="space-y-4">
            {/* Agent status */}
            <div className="cortex-card">
              <div className="section-header">
                <div>
                  <h2 className="text-sm font-semibold text-cortex-text">Agents</h2>
                  <p className="text-xs text-cortex-muted">{agentsData?.total ?? 0} total</p>
                </div>
                <a href="/agents" className="text-xs text-cortex-accent hover:underline">Manage</a>
              </div>
              <AgentStatusWidget
                agents={agentsData?.agents ?? []}
                isLoading={agentsLoading}
              />
            </div>

            {/* Cost breakdown */}
            <div className="cortex-card">
              <div className="section-header">
                <h2 className="text-sm font-semibold text-cortex-text">LLM Costs</h2>
                <span className="text-xs text-cortex-muted">This month</span>
              </div>
              <CostTracker
                data={financeData?.modelCosts ?? []}
                isLoading={financeLoading}
              />
            </div>

            {/* System health */}
            <div className="cortex-card">
              <div className="section-header">
                <h2 className="text-sm font-semibold text-cortex-text">System Health</h2>
              </div>
              <SystemHealthWidget
                health={health}
                isLoading={!health && statsLoading}
              />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
