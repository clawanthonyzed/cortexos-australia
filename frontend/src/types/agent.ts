export type AgentStatus = "idle" | "running" | "paused" | "error" | "stopped";

export type AgentCapability =
  | "web_search"
  | "code_execution"
  | "file_operations"
  | "email"
  | "database"
  | "api_calls"
  | "image_generation"
  | "data_analysis";

export interface AgentMetrics {
  successRate: number;
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  totalCostUsd: number;
  totalTokensUsed: number;
  averageTaskDurationMs: number;
  lastRunAt: string | null;
  uptimePercent: number;
}

export interface AgentMemory {
  sizeBytes: number;
  entryCount: number;
  lastUpdatedAt: string | null;
}

export interface Agent {
  id: string;
  name: string;
  slug: string;
  purpose: string;
  description: string;
  status: AgentStatus;
  model: string;
  capabilities: AgentCapability[];
  currentTask: string | null;
  currentTaskId: string | null;
  venture: string | null;
  tags: string[];
  metrics: AgentMetrics;
  memory: AgentMemory;
  config: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface AgentLog {
  id: string;
  agentId: string;
  level: "debug" | "info" | "warn" | "error";
  message: string;
  metadata: Record<string, unknown> | null;
  timestamp: string;
}

export interface CreateAgentInput {
  name: string;
  purpose: string;
  description: string;
  model: string;
  capabilities: AgentCapability[];
  venture: string | null;
  tags: string[];
  config: Record<string, unknown>;
}

export interface UpdateAgentInput extends Partial<CreateAgentInput> {
  status?: AgentStatus;
}
