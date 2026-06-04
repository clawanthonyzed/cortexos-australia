"use client";

import { useState } from "react";
import { Plus, Search, Filter, ListTodo, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { TaskRow } from "@/components/tasks/task-row";
import { TaskForm } from "@/components/tasks/task-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { Badge } from "@/components/ui/badge";
import { useTasks, useTaskStats } from "@/hooks/use-tasks";
import type { TaskStatus } from "@/types/task";
import { mutate } from "swr";

export default function TasksPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useTasks({
    search: search || undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
    page,
    pageSize: 25,
  });
  const { data: stats } = useTaskStats();

  const tasks = data?.tasks ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / 25);

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Tasks</h1>
            <p className="text-sm text-cortex-muted mt-0.5">
              {isLoading ? "Loading..." : `${total} tasks`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => mutate((key: string) => key.startsWith("/tasks"))}
              aria-label="Refresh tasks"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              New Task
            </Button>
          </div>
        </div>

        {/* Stats bar */}
        {stats && (
          <div className="flex items-center gap-4 text-xs text-cortex-muted flex-wrap">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cortex-warning" />
              {stats.queued} queued
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cortex-success animate-pulse" />
              {stats.running} running
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-cortex-muted" />
              {stats.completedToday} completed today
            </span>
            {stats.failedToday > 0 && (
              <span className="flex items-center gap-1.5 text-cortex-error">
                <span className="h-2 w-2 rounded-full bg-cortex-error" />
                {stats.failedToday} failed today
              </span>
            )}
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cortex-muted" />
            <Input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search tasks..."
              className="pl-9"
            />
          </div>
          <Select
            value={statusFilter}
            onValueChange={(v) => { setStatusFilter(v as TaskStatus | "all"); setPage(1); }}
          >
            <SelectTrigger className="w-44">
              <Filter className="h-3.5 w-3.5 mr-1 text-cortex-muted" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="queued">Queued</SelectItem>
              <SelectItem value="running">Running</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Table */}
        <div className="rounded-lg border border-cortex-border bg-cortex-surface overflow-hidden">
          {/* Table header */}
          <div className="hidden sm:flex items-center gap-3 px-4 py-2 border-b border-cortex-border bg-cortex-bg/30">
            <span className="w-4" />
            <span className="flex-1 text-[11px] font-semibold uppercase tracking-wider text-cortex-muted">Task</span>
            <span className="hidden sm:block w-24 text-right text-[11px] font-semibold uppercase tracking-wider text-cortex-muted">Duration</span>
            <span className="hidden md:block w-16 text-right text-[11px] font-semibold uppercase tracking-wider text-cortex-muted">Cost</span>
            <span className="hidden sm:block w-16 text-[11px] font-semibold uppercase tracking-wider text-cortex-muted">Priority</span>
            <span className="w-16" />
            <span className="w-4" />
          </div>

          {isLoading ? (
            <div className="divide-y divide-cortex-border">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3 px-4 py-3">
                  <Skeleton className="h-4 w-4 rounded-full" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-3 w-48" />
                    <Skeleton className="h-2.5 w-28" />
                  </div>
                  <Skeleton className="h-3 w-12" />
                  <Skeleton className="h-3 w-10" />
                </div>
              ))}
            </div>
          ) : tasks.length === 0 ? (
            <EmptyState
              icon={ListTodo}
              title="No tasks found"
              description={search ? `No tasks matching "${search}"` : "Queue your first task to get started"}
              action={!search ? { label: "Create Task", onClick: () => setCreateOpen(true) } : undefined}
            />
          ) : (
            <div>
              {tasks.map((task) => (
                <TaskRow key={task.id} task={task} />
              ))}
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between text-sm">
            <p className="text-cortex-muted">
              Page {page} of {totalPages} · {total} tasks
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Create dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Create Task</DialogTitle>
          </DialogHeader>
          <TaskForm
            onSuccess={() => setCreateOpen(false)}
            onCancel={() => setCreateOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
