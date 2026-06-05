import useSWR, { type SWRConfiguration } from "swr";
import useSWRMutation from "swr/mutation";
import { fetcher, apiClient } from "@/lib/api";
import type { Workflow, CreateWorkflowInput, WorkflowRun, WorkflowNode, WorkflowEdge } from "@/types/workflow";

const WORKFLOWS_KEY = "/workflows";

/** Matches WorkflowReadBrief from backend */
interface WorkflowBrief {
  id: string;
  name: string;
  status: string;
  trigger_type: string;
  run_count: number;
  created_at: string;
}

/** Matches WorkflowRead from backend */
interface WorkflowFull {
  id: string;
  name: string;
  description: string | null;
  status: string;
  run_count: number;
  success_count: number;
  failure_count: number;
  graph_json: {
    nodes?: WorkflowNode[];
    edges?: WorkflowEdge[];
  };
  trigger_type: string;
  cron_expression: string | null;
  config_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface WorkflowsBackendResponse {
  items: WorkflowBrief[];
  total: number;
  page: number;
  page_size: number;
}

interface WorkflowsResponse {
  workflows: Workflow[];
  total: number;
}

interface WorkflowRunsResponse {
  runs: WorkflowRun[];
  total: number;
}

function adaptBrief(b: WorkflowBrief): Workflow {
  return {
    id: b.id,
    name: b.name,
    description: "",
    status: b.status as Workflow["status"],
    venture: null,
    tags: [],
    nodes: [],
    edges: [],
    runCount: b.run_count,
    lastRunAt: null,
    lastRunStatus: null,
    avgDurationMs: null,
    createdAt: b.created_at,
    updatedAt: b.created_at,
  };
}

function adaptFull(b: WorkflowFull): Workflow {
  return {
    id: b.id,
    name: b.name,
    description: b.description ?? "",
    status: b.status as Workflow["status"],
    venture: null,
    tags: [],
    nodes: b.graph_json?.nodes ?? [],
    edges: b.graph_json?.edges ?? [],
    runCount: b.run_count,
    lastRunAt: null,
    lastRunStatus: b.failure_count > 0 ? "failed" : b.success_count > 0 ? "completed" : null,
    avgDurationMs: null,
    createdAt: b.created_at,
    updatedAt: b.updated_at,
  };
}

async function workflowsFetcher(url: string): Promise<WorkflowsResponse> {
  const raw = await fetcher<WorkflowsBackendResponse>(url);
  return {
    workflows: raw.items.map(adaptBrief),
    total: raw.total,
  };
}

async function workflowFetcher(url: string): Promise<Workflow> {
  const raw = await fetcher<WorkflowFull>(url);
  return adaptFull(raw);
}

export function useWorkflows(
  params?: { status?: string; venture?: string; search?: string },
  config?: SWRConfiguration
) {
  const searchParams = new URLSearchParams();
  if (params?.status && params.status !== "all") searchParams.set("status", params.status);

  const key = `${WORKFLOWS_KEY}?${searchParams.toString()}`;
  return useSWR<WorkflowsResponse>(key, workflowsFetcher, { refreshInterval: 10000, ...config });
}

export function useWorkflow(id: string | null, config?: SWRConfiguration) {
  return useSWR<Workflow>(id ? `${WORKFLOWS_KEY}/${id}` : null, workflowFetcher, config);
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
      return apiClient.post<WorkflowFull>(WORKFLOWS_KEY, {
        name: arg.name,
        description: arg.description,
        graph_json: { nodes: arg.nodes, edges: arg.edges },
      }).then(adaptFull);
    }
  );
}

export function useUpdateWorkflow(id: string) {
  return useSWRMutation(
    `${WORKFLOWS_KEY}/${id}`,
    async (key: string, { arg }: { arg: Partial<CreateWorkflowInput> & { status?: string } }) => {
      const body: Record<string, unknown> = {};
      if (arg.name) body.name = arg.name;
      if (arg.description !== undefined) body.description = arg.description;
      if (arg.nodes || arg.edges) body.graph_json = { nodes: arg.nodes ?? [], edges: arg.edges ?? [] };
      if (arg.status) body.status = arg.status;
      return apiClient.put<WorkflowFull>(key, body).then(adaptFull);
    }
  );
}

export function useRunWorkflow(id: string) {
  return useSWRMutation(`${WORKFLOWS_KEY}/${id}/execute`, async (key: string) => {
    return apiClient.post<{ workflow_id: string; run_id: string; status: string }>(key, { async_run: true });
  });
}

export function useDeleteWorkflow(id: string) {
  return useSWRMutation(`${WORKFLOWS_KEY}/${id}`, async (key: string) => {
    return apiClient.delete<void>(key);
  });
}
