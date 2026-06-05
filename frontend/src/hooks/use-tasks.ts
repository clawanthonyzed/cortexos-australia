import useSWR, { type SWRConfiguration } from "swr";
import useSWRMutation from "swr/mutation";
import { fetcher, apiClient } from "@/lib/api";
import type { Task, CreateTaskInput, TaskPriority, TaskQueueStats } from "@/types/task";

const TASKS_KEY = "/tasks";

/** Matches TaskReadBrief from backend (list endpoint) */
interface TaskBrief {
  id: string;
  title: string;
  status: string;
  priority: number;
  agent_id: string | null;
  created_at: string;
}

/** Matches TaskRead from backend (detail endpoint) */
interface TaskFull {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: number;
  input_data: Record<string, unknown>;
  agent_id: string | null;
  workflow_id: string | null;
  error_message: string | null;
  result_json: Record<string, unknown> | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

interface TasksBackendResponse {
  items: TaskBrief[];
  total: number;
  page: number;
  page_size: number;
}

interface TasksResponse {
  tasks: Task[];
  total: number;
  page: number;
  pageSize: number;
}

function intToPriority(p: number): TaskPriority {
  if (p >= 9) return "critical";
  if (p >= 7) return "high";
  if (p >= 4) return "normal";
  return "low";
}

function adaptTaskBrief(b: TaskBrief): Task {
  return {
    id: b.id,
    title: b.title,
    description: "",
    status: b.status as Task["status"],
    priority: intToPriority(b.priority),
    agentId: b.agent_id,
    agentName: null,
    workflowId: null,
    venture: null,
    tags: [],
    steps: [],
    input: {},
    output: null,
    errorMessage: null,
    tokensUsed: 0,
    costUsd: 0,
    progressPercent: 0,
    queuedAt: b.created_at,
    startedAt: null,
    completedAt: null,
    durationMs: null,
    createdAt: b.created_at,
    updatedAt: b.created_at,
  };
}

function adaptTaskFull(b: TaskFull): Task {
  const durationMs =
    b.started_at && b.completed_at
      ? new Date(b.completed_at).getTime() - new Date(b.started_at).getTime()
      : null;

  return {
    id: b.id,
    title: b.title,
    description: b.description ?? "",
    status: b.status as Task["status"],
    priority: intToPriority(b.priority),
    agentId: b.agent_id,
    agentName: null,
    workflowId: b.workflow_id,
    venture: null,
    tags: [],
    steps: [],
    input: b.input_data,
    output: b.result_json,
    errorMessage: b.error_message,
    tokensUsed: 0,
    costUsd: 0,
    progressPercent: b.status === "completed" ? 100 : b.status === "running" ? 50 : 0,
    queuedAt: b.created_at,
    startedAt: b.started_at,
    completedAt: b.completed_at,
    durationMs,
    createdAt: b.created_at,
    updatedAt: b.updated_at,
  };
}

async function tasksFetcher(url: string): Promise<TasksResponse> {
  const raw = await fetcher<TasksBackendResponse>(url);
  return {
    tasks: raw.items.map(adaptTaskBrief),
    total: raw.total,
    page: raw.page,
    pageSize: raw.page_size,
  };
}

async function taskFetcher(url: string): Promise<Task> {
  const raw = await fetcher<TaskFull>(url);
  return adaptTaskFull(raw);
}

export function useTasks(
  params?: {
    status?: string;
    agentId?: string;
    venture?: string;
    search?: string;
    page?: number;
    pageSize?: number;
  },
  config?: SWRConfiguration
) {
  const searchParams = new URLSearchParams();
  if (params?.status && params.status !== "all") searchParams.set("status", params.status);
  if (params?.agentId) searchParams.set("agent_id", params.agentId);
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.pageSize) searchParams.set("page_size", String(params.pageSize));

  const key = `${TASKS_KEY}?${searchParams.toString()}`;

  return useSWR<TasksResponse>(key, tasksFetcher, {
    refreshInterval: 3000,
    ...config,
  });
}

export function useTask(id: string | null, config?: SWRConfiguration) {
  return useSWR<Task>(id ? `${TASKS_KEY}/${id}` : null, taskFetcher, {
    refreshInterval: 2000,
    ...config,
  });
}

export function useTaskStats(config?: SWRConfiguration) {
  return useSWR<TaskQueueStats>(`${TASKS_KEY}/stats`, fetcher, {
    refreshInterval: 5000,
    ...config,
  });
}

export function useCreateTask() {
  return useSWRMutation(
    TASKS_KEY,
    async (_key: string, { arg }: { arg: CreateTaskInput }) => {
      const priorityMap: Record<TaskPriority, number> = {
        critical: 10, high: 8, normal: 5, low: 2,
      };
      return apiClient.post<TaskFull>(TASKS_KEY, {
        title: arg.title,
        description: arg.description,
        input_data: arg.input,
        agent_id: arg.agentId,
        workflow_id: arg.workflowId,
        priority: priorityMap[arg.priority] ?? 5,
      }).then(adaptTaskFull);
    }
  );
}

export function useCancelTask(id: string) {
  return useSWRMutation(`${TASKS_KEY}/${id}/cancel`, async (key: string) => {
    return apiClient.post<TaskFull>(key).then(adaptTaskFull);
  });
}

export function useRetryTask(id: string) {
  return useSWRMutation(`${TASKS_KEY}/${id}/retry`, async (key: string) => {
    return apiClient.post<TaskFull>(key).then(adaptTaskFull);
  });
}
