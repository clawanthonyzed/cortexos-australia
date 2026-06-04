import useSWR, { type SWRConfiguration } from "swr";
import useSWRMutation from "swr/mutation";
import { fetcher, apiClient } from "@/lib/api";
import type { Task, CreateTaskInput, TaskQueueStats } from "@/types/task";

const TASKS_KEY = "/tasks";

interface TasksResponse {
  tasks: Task[];
  total: number;
  page: number;
  pageSize: number;
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
  if (params?.agentId) searchParams.set("agentId", params.agentId);
  if (params?.venture && params.venture !== "all") searchParams.set("venture", params.venture);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.page) searchParams.set("page", String(params.page));
  if (params?.pageSize) searchParams.set("pageSize", String(params.pageSize));

  const key = `${TASKS_KEY}?${searchParams.toString()}`;

  return useSWR<TasksResponse>(key, fetcher, {
    refreshInterval: 3000,
    ...config,
  });
}

export function useTask(id: string | null, config?: SWRConfiguration) {
  return useSWR<Task>(id ? `${TASKS_KEY}/${id}` : null, fetcher, {
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
      return apiClient.post<Task>(TASKS_KEY, arg);
    }
  );
}

export function useCancelTask(id: string) {
  return useSWRMutation(`${TASKS_KEY}/${id}/cancel`, async (key: string) => {
    return apiClient.post<Task>(key);
  });
}

export function useRetryTask(id: string) {
  return useSWRMutation(`${TASKS_KEY}/${id}/retry`, async (key: string) => {
    return apiClient.post<Task>(key);
  });
}
