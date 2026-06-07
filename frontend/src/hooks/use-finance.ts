import useSWR, { type SWRConfiguration } from "swr";
import { useEffect } from "react";
import { fetcher, healthFetcher } from "@/lib/api";
import type { FinanceDashboard } from "@/types/finance";
import { useSystemStore } from "@/store/system-store";

export function useFinance(
  params?: { period?: "7d" | "30d" | "90d" | "1y" },
  config?: SWRConfiguration
) {
  const searchParams = new URLSearchParams();
  if (params?.period) searchParams.set("period", params.period);

  const key = `/finance/dashboard?${searchParams.toString()}`;
  return useSWR<FinanceDashboard>(key, fetcher, {
    refreshInterval: 30000,
    ...config,
  });
}

interface ReadyResponse {
  status: string;
  checks: { database: string; redis: string };
  uptime_seconds: number;
}

export function useSystemHealth() {
  const { setHealth } = useSystemStore();
  const start = typeof performance !== "undefined" ? performance.now() : 0;

  const { data } = useSWR<ReadyResponse>("/ready", healthFetcher, {
    refreshInterval: 15000,
    onSuccess: (d) => {
      const latency = Math.round(performance.now() - start);
      setHealth({
        overallPercent: d.status === "ready" ? 100 : 90,
        apiLatencyMs: latency,
        dbHealthy: d.checks.database === "ok",
        wsHealthy: false,
        agentServiceHealthy: d.status === "ready",
        queueDepth: 0,
        lastCheckedAt: new Date().toISOString(),
      });
    },
  });
  return data;
}

export function useDashboardStats(config?: SWRConfiguration) {
  return useSWR<{
    activeAgents: number;
    activeAgentsDelta: number;
    revenueThisMonthAud: number;
    revenueGrowthPercent: number;
    costsThisMonthUsd: number;
    costsGrowthPercent: number;
    tasksCompletedToday: number;
    tasksCompletedDelta: number;
    tokenUsageTodayM: number;
    tokenUsageDeltaPercent: number;
    systemHealthPercent: number;
  }>("/dashboard/stats", fetcher, {
    refreshInterval: 10000,
    ...config,
  });
}
