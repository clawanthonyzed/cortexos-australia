"use client";

import { useState } from "react";
import { Plus, Search, GitFork } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { WorkflowCard } from "@/components/workflows/workflow-card";
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
  DialogDescription,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useWorkflows, useCreateWorkflow } from "@/hooks/use-workflows";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { mutate } from "swr";

export default function WorkflowsPage() {
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const router = useRouter();

  const { data, isLoading } = useWorkflows({
    search: search || undefined,
    status: statusFilter !== "all" ? statusFilter : undefined,
  });

  const { trigger: createWorkflow, isMutating: creating } = useCreateWorkflow();

  const workflows = data?.workflows ?? [];

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const wf = await createWorkflow({
        name: newName.trim(),
        description: newDescription.trim(),
        venture: null,
        tags: [],
        nodes: [
          {
            id: "start-1",
            type: "start",
            position: { x: 250, y: 50 },
            data: { label: "Start", nodeType: "start" },
          },
          {
            id: "end-1",
            type: "end",
            position: { x: 250, y: 350 },
            data: { label: "End", nodeType: "end" },
          },
        ],
        edges: [],
      });
      await mutate("/workflows");
      toast.success("Workflow created");
      setCreateOpen(false);
      router.push(`/workflows/${wf.id}`);
    } catch {
      toast.error("Failed to create workflow");
    }
  };

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Workflows</h1>
            <p className="text-sm text-cortex-muted mt-0.5">
              {isLoading ? "Loading..." : `${data?.total ?? 0} workflows`}
            </p>
          </div>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" />
            New Workflow
          </Button>
        </div>

        {/* Filters */}
        <div className="flex gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cortex-muted" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search workflows..."
              className="pl-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-cortex-border bg-cortex-surface p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-8 w-8 rounded-lg" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-3.5 w-24" />
                    <Skeleton className="h-3 w-36" />
                  </div>
                </div>
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ))}
          </div>
        ) : workflows.length === 0 ? (
          <EmptyState
            icon={GitFork}
            title="No workflows found"
            description="Build your first workflow to automate multi-step agent processes"
            action={{ label: "Create Workflow", onClick: () => setCreateOpen(true) }}
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {workflows.map((wf) => (
              <WorkflowCard key={wf.id} workflow={wf} />
            ))}
          </div>
        )}
      </div>

      {/* Create dialog */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create Workflow</DialogTitle>
            <DialogDescription>Give your workflow a name, then build it in the visual editor.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-cortex-text">Name</label>
              <Input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. Content Pipeline"
                autoFocus
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-cortex-text">Description</label>
              <Input
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Optional description"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button onClick={handleCreate} disabled={creating || !newName.trim()}>
                {creating ? "Creating..." : "Create & Open Editor"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
