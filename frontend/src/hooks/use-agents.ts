import useSWR, { type SWRConfiguration } from "swr";
import useSWRMutation from "swr/mutation";
import { fetcher, apiClient } from "@/lib/api";
import type { Agent, CreateAgentInput, UpdateAgentInput, AgentLog } from "@/types/agent";

const AGENTS_KEY = "/agents";

/** Matches AgentReadBrief from backend (list endpoint) */
interface AgentBrief {
  id: string;
  name: string;
  purpose: string;
  status: string;
  model_provider: string;
  model_name: string;
  agent_type: string;
}

/** Matches AgentRead from backend (detail endpoint) */
interface AgentFull extends AgentBrief {
  description: string | null;
  temperature: number;
  max_tokens: number;
  config_json: Record<string, unknown>;
  system_prompt: string | null;
  tags: string[];
  total_tokens_used: number;
  total_cost_usd: number;
  success_count: number;
  error_count: number;
  last_run_at: string | null;
  created_at: string;
  updated_at: string;
}

interface AgentsBackendResponse {
  items: AgentBrief[];
  total: number;
  page: number;
  page_size: number;
}

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

function adaptBrief(b: AgentBrief): Agent {
  return {
    id: b.id,
    name: b.name,
    slug: b.name.toLowerCase().replace(/\s+/g, "-"),
    purpose: b.purpose,
    description: "",
    status: b.status as Agent["status"],
    model: `${b.model_provider}/${b.model_name}`,
    capabilities: [],
    currentTask: null,
    currentTaskId: null,
    venture: null,
    tags: [],
    metrics: {
      successRate: 100,
      totalTasks: 0,
      completedTasks: 0,
      failedTasks: 0,
      totalCostUsd: 0,
      totalTokensUsed: 0,
      averageTaskDurationMs: 0,
      lastRunAt: null,
      uptimePercent: 100,
    },
    memory: { sizeBytes: 0, entryCount: 0, lastUpdatedAt: null },
    config: {},
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

function adaptFull(b: AgentFull): Agent {
  const totalTasks = b.success_count + b.error_count;
  const successRate = totalTasks > 0 ? (b.success_count / totalTasks) * 100 : 100;

  let tags: string[] = [];
  try {
    tags = typeof b.tags === "string" ? JSON.parse(b.tags as string) : (b.tags ?? []);
  } catch { tags = []; }

  let config: Record<string, unknown> = {};
  try {
    config = typeof b.config_json === "string" ? JSON.parse(b.config_json as string) : (b.config_json ?? {});
  } catch { config = {}; }

  return {
    id: b.id,
    name: b.name,
    slug: b.name.toLowerCase().replace(/\s+/g, "-"),
    purpose: b.purpose,
    description: b.description ?? "",
    status: b.status as Agent["status"],
    model: `${b.model_provider}/${b.model_name}`,
    capabilities: [],
    currentTask: null,
    currentTaskId: null,
    venture: null,
    tags,
    metrics: {
      successRate,
      totalTasks,
      completedTasks: b.success_count,
      failedTasks: b.error_count,
      totalCostUsd: b.total_cost_usd,
      totalTokensUsed: b.total_tokens_used,
      averageTaskDurationMs: 0,
      lastRunAt: b.last_run_at,
      uptimePercent: 100,
    },
    memory: { sizeBytes: 0, entryCount: 0, lastUpdatedAt: null },
    config,
    createdAt: b.created_at,
    updatedAt: b.updated_at,
  };
}

async function agentsFetcher(url: string): Promise<AgentsResponse> {
  const raw = await fetcher<AgentsBackendResponse>(url);
  return {
    agents: raw.items.map(adaptBrief),
    total: raw.total,
    page: raw.page,
    pageSize: raw.page_size,
  };
}

async function agentFetcher(url: string): Promise<Agent> {
  const raw = await fetcher<AgentFull>(url);
  return adaptFull(raw);
}

export function useAgents(
  params?: { status?: string; venture?: string; search?: string; page?: number },
  config?: SWRConfiguration
) {
  const searchParams = new URLSearchParams();
  if (params?.status && params.status !== "all") searchParams.set("status", params.status);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.page) searchParams.set("page", String(params.page));

  const key = `${AGENTS_KEY}?${searchParams.toString()}`;

  return useSWR<AgentsResponse>(key, agentsFetcher, {
    refreshInterval: 5000,
    ...config,
  });
}

export function useAgent(id: string | null, config?: SWRConfiguration) {
  return useSWR<Agent>(id ? `${AGENTS_KEY}/${id}` : null, agentFetcher, {
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
      return apiClient.post<AgentFull>(AGENTS_KEY, {
        name: arg.name,
        purpose: arg.purpose,
        description: arg.description,
        model_provider: arg.model?.split("/")[0] ?? "claude",
        model_name: arg.model?.split("/").slice(1).join("/") ?? "claude-sonnet-4-6",
        tags: arg.tags,
        config_json: arg.config,
      }).then(adaptFull);
    }
  );
}

export function useUpdateAgent(id: string) {
  return useSWRMutation(
    `${AGENTS_KEY}/${id}`,
    async (key: string, { arg }: { arg: UpdateAgentInput }) => {
      const body: Record<string, unknown> = {};
      if (arg.name) body.name = arg.name;
      if (arg.purpose) body.purpose = arg.purpose;
      if (arg.description !== undefined) body.description = arg.description;
      if (arg.model) {
        const parts = arg.model.split("/");
        body.model_provider = parts[0];
        body.model_name = parts.slice(1).join("/");
      }
      if (arg.tags) body.tags = arg.tags;
      if (arg.config) body.config_json = arg.config;
      if (arg.status) body.status = arg.status;
      return apiClient.patch<AgentFull>(key, body).then(adaptFull);
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
    `${AGENTS_KEY}/${id}`,
    async (_key: string, { arg }: { arg: "start" | "stop" | "pause" }) => {
      const endpoint =
        arg === "start" ? `${AGENTS_KEY}/${id}/run` :
        arg === "stop"  ? `${AGENTS_KEY}/${id}/stop` :
                          `${AGENTS_KEY}/${id}/pause`;
      return apiClient.post<AgentFull>(endpoint, arg === "start" ? { task: "Manual start", async_run: true } : {}).then(adaptFull);
    }
  );
}
