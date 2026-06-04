"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { WorkflowBuilder } from "@/components/workflows/workflow-builder";
import { PageLoader } from "@/components/ui/loading-spinner";
import { useWorkflow } from "@/hooks/use-workflows";

export default function WorkflowBuilderPage() {
  const params = useParams();
  const id = params.id as string;
  const { data: workflow, isLoading } = useWorkflow(id);

  if (isLoading) {
    return (
      <AppShell>
        <PageLoader label="Loading workflow..." />
      </AppShell>
    );
  }

  if (!workflow) {
    return (
      <AppShell>
        <div className="flex items-center justify-center h-64 text-cortex-muted text-sm">
          Workflow not found
        </div>
      </AppShell>
    );
  }

  return (
    // Full-screen builder — no AppShell padding constraints
    <div className="flex h-screen w-screen overflow-hidden bg-cortex-bg">
      <WorkflowBuilder workflow={workflow} />
    </div>
  );
}
