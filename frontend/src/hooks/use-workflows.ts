import useSWR, { type SWRConfiguration } from "swr";
import useSWRMutation from "swr/mutation";
import { fetcher, apiClient } from "@/lib/api";
import type { Workflow, CreateWorkflowInput, WorkflowRun } from "@/types/workflow";

const WORKFLOWS_KEY = "/workflows";

interface WorkflowsResponse {
  workflows: Workflow[];
  total: number;
}

interface WorkflowRunsResponse {
  runs: WorkflowRun[];
  total: number;
}

export function useWorkflows(
  params?: { status?: string; venture?: string; search?: string },
  config?: SWRConfiguration
) {
  const searchParams = new URLSearchParams();
  if (params?.status && params.status !== "all") searchParams.set("status", params.status);
  if (params?.venture && params.venture !== "all") searchParams.set("venture", params.venture);
  if (params?.search) searchParams.set("search", params.search);

  const key = `${WORKFLOWS_KEY}?${searchParams.toString()}`;
  return useSWR<WorkflowsResponse>(key, fetcher, { refreshInterval: 10000, ...config });
}

export function useWorkflow(id: string | null, config?: SWRConfiguration) {
  return useSWR<Workflow>(id ? `${WORKFLOWS_KEY}/${id}` : null, fetcher, config);
}

export function useWorkflowRuns(workflowId: string | null, config?: SWRConfiguration) {
  return useSWR<WorkflowRunsResponse>(
    workflowId ? `${WORKFLOWS_KEY}/${workflowId}/runs` : null,
    fetcher,
    { refreshInterval: 5000, ...config }
  );
}

export function useCreateWorkflow() {
  return useSWRMutation(
    WORKFLOWS_KEY,
    async (_key: string, { arg }: { arg: CreateWorkflowInput }) => {
      return apiClient.post<Workflow>(WORKFLOWS_KEY, arg);
    }
  );
}

export function useUpdateWorkflow(id: string) {
  return useSWRMutation(
    `${WORKFLOWS_KEY}/${id}`,
    async (key: string, { arg }: { arg: Partial<CreateWorkflowInput> & { status?: string } }) => {
      return apiClient.put<Workflow>(key, arg);
    }
  );
}

export function useRunWorkflow(id: string) {
  return useSWRMutation(`${WORKFLOWS_KEY}/${id}/run`, async (key: string) => {
    return apiClient.post<WorkflowRun>(key);
  });
}

export function useDeleteWorkflow(id: string) {
  return useSWRMutation(`${WORKFLOWS_KEY}/${id}`, async (key: string) => {
    return apiClient.delete<void>(key);
  });
}
