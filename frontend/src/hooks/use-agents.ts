import useSWR, { type SWRConfiguration } from "swr";
import useSWRMutation from "swr/mutation";
import { fetcher, apiClient } from "@/lib/api";
import type { Agent, CreateAgentInput, UpdateAgentInput, AgentLog } from "@/types/agent";

const AGENTS_KEY = "/agents";

interface AgentsResponse {
  agents: Agent[];
  total: number;
  page: number;
  pageSize: number;
}

interface AgentLogsResponse {
  logs: AgentLog[];
  total: number;
}

export function useAgents(
  params?: { status?: string; venture?: string; search?: string; page?: number },
  config?: SWRConfiguration
) {
  const searchParams = new URLSearchParams();
  if (params?.status && params.status !== "all") searchParams.set("status", params.status);
  if (params?.venture && params.venture !== "all") searchParams.set("venture", params.venture);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.page) searchParams.set("page", String(params.page));

  const key = `${AGENTS_KEY}?${searchParams.toString()}`;

  return useSWR<AgentsResponse>(key, fetcher, {
    refreshInterval: 5000,
    ...config,
  });
}

export function useAgent(id: string | null, config?: SWRConfiguration) {
  return useSWR<Agent>(id ? `${AGENTS_KEY}/${id}` : null, fetcher, {
    refreshInterval: 3000,
    ...config,
  });
}

export function useAgentLogs(agentId: string | null, config?: SWRConfiguration) {
  return useSWR<AgentLogsResponse>(
    agentId ? `${AGENTS_KEY}/${agentId}/logs` : null,
    fetcher,
    {
      refreshInterval: 2000,
      ...config,
    }
  );
}

export function useCreateAgent() {
  return useSWRMutation(
    AGENTS_KEY,
    async (_key: string, { arg }: { arg: CreateAgentInput }) => {
      return apiClient.post<Agent>(AGENTS_KEY, arg);
    }
  );
}

export function useUpdateAgent(id: string) {
  return useSWRMutation(
    `${AGENTS_KEY}/${id}`,
    async (key: string, { arg }: { arg: UpdateAgentInput }) => {
      return apiClient.patch<Agent>(key, arg);
    }
  );
}

export function useDeleteAgent(id: string) {
  return useSWRMutation(`${AGENTS_KEY}/${id}`, async (key: string) => {
    return apiClient.delete<void>(key);
  });
}

export function useAgentAction(id: string) {
  return useSWRMutation(
    `${AGENTS_KEY}/${id}/action`,
    async (key: string, { arg }: { arg: "start" | "stop" | "pause" }) => {
      return apiClient.post<Agent>(key, { action: arg });
    }
  );
}
