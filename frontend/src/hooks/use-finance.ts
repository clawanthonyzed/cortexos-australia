import useSWR, { type SWRConfiguration } from "swr";
import { fetcher } from "@/lib/api";
import type { FinanceDashboard } from "@/types/finance";

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
