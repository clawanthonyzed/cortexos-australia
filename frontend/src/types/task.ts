export type TaskStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "paused";

export type TaskPriority = "low" | "normal" | "high" | "critical";

export interface TaskStep {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  output: string | null;
  errorMessage: string | null;
  startedAt: string | null;
  completedAt: string | null;
  durationMs: number | null;
  tokensUsed: number | null;
  costUsd: number | null;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  agentId: string | null;
  agentName: string | null;
  workflowId: string | null;
  venture: string | null;
  tags: string[];
  steps: TaskStep[];
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  errorMessage: string | null;
  tokensUsed: number;
  costUsd: number;
  progressPercent: number;
  queuedAt: string;
  startedAt: string | null;
  completedAt: string | null;
  durationMs: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateTaskInput {
  title: string;
  description: string;
  priority: TaskPriority;
  agentId: string | null;
  workflowId: string | null;
  venture: string | null;
  tags: string[];
  input: Record<string, unknown>;
}

export interface TaskQueueStats {
  queued: number;
  running: number;
  completedToday: number;
  failedToday: number;
  avgDurationMs: number;
  totalCostToday: number;
}
