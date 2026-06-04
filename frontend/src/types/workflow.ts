export type WorkflowStatus = "draft" | "active" | "paused" | "archived";

export type NodeType =
  | "start"
  | "end"
  | "agent"
  | "condition"
  | "approval"
  | "webhook"
  | "delay";

export interface WorkflowNodeData {
  label: string;
  nodeType: NodeType;
  agentId?: string;
  agentName?: string;
  promptTemplate?: string;
  conditions?: ConditionRule[];
  approvers?: string[];
  webhookUrl?: string;
  delayMs?: number;
  config?: Record<string, unknown>;
}

export interface ConditionRule {
  id: string;
  field: string;
  operator: "eq" | "neq" | "gt" | "lt" | "gte" | "lte" | "contains" | "not_contains";
  value: string;
  logicalOp?: "and" | "or";
}

export interface WorkflowNode {
  id: string;
  type: NodeType;
  position: { x: number; y: number };
  data: WorkflowNodeData;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string | null;
  targetHandle?: string | null;
  label?: string;
  animated?: boolean;
}

export interface WorkflowRun {
  id: string;
  workflowId: string;
  status: "running" | "completed" | "failed" | "cancelled";
  startedAt: string;
  completedAt: string | null;
  tokensUsed: number;
  costUsd: number;
  output: Record<string, unknown> | null;
  errorMessage: string | null;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  status: WorkflowStatus;
  venture: string | null;
  tags: string[];
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  runCount: number;
  lastRunAt: string | null;
  lastRunStatus: "completed" | "failed" | null;
  avgDurationMs: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateWorkflowInput {
  name: string;
  description: string;
  venture: string | null;
  tags: string[];
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}
