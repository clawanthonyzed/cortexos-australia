"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type ReactFlowInstance,
  BackgroundVariant,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";
import type { Workflow, WorkflowNode, WorkflowEdge, NodeType, WorkflowNodeData } from "@/types/workflow";
import { AgentNode } from "./nodes/agent-node";
import { ConditionNode } from "./nodes/condition-node";
import { ApprovalNode } from "./nodes/approval-node";
import { NodePalette } from "./node-palette";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useUpdateWorkflow, useRunWorkflow } from "@/hooks/use-workflows";
import { generateId } from "@/lib/utils";
import { toast } from "sonner";
import { Save, Play, ArrowLeft, Settings } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

// Start/End node components
function StartNode({ selected }: { selected: boolean }) {
  return (
    <div className={cn("flex h-10 w-10 items-center justify-center rounded-full border-2 bg-cortex-surface", selected ? "border-cortex-accent" : "border-cortex-muted/40")}>
      <span className="text-[9px] font-bold text-cortex-muted uppercase tracking-wider">Start</span>
    </div>
  );
}

function EndNode({ selected }: { selected: boolean }) {
  return (
    <div className={cn("flex h-10 w-10 items-center justify-center rounded-full border-4 bg-cortex-surface", selected ? "border-cortex-accent" : "border-cortex-muted/40")}>
      <span className="text-[9px] font-bold text-cortex-muted uppercase tracking-wider">End</span>
    </div>
  );
}

const nodeTypes = {
  agent: AgentNode,
  condition: ConditionNode,
  approval: ApprovalNode,
  start: StartNode as React.ComponentType<{ selected: boolean }>,
  end: EndNode as React.ComponentType<{ selected: boolean }>,
};

const defaultEdgeStyle = {
  stroke: "#1e1e24",
  strokeWidth: 2,
};

const selectedEdgeStyle = {
  stroke: "#6366f1",
  strokeWidth: 2,
};

function toReactFlowNodes(nodes: WorkflowNode[]) {
  return nodes.map((n) => ({
    id: n.id,
    type: n.type,
    position: n.position,
    data: n.data,
  }));
}

function toReactFlowEdges(edges: WorkflowEdge[]) {
  return edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    sourceHandle: e.sourceHandle ?? undefined,
    targetHandle: e.targetHandle ?? undefined,
    label: e.label,
    animated: e.animated ?? false,
    style: defaultEdgeStyle,
    markerEnd: { type: MarkerType.ArrowClosed, color: "#1e1e24" },
  }));
}

interface WorkflowBuilderProps {
  workflow: Workflow;
}

export function WorkflowBuilder({ workflow }: WorkflowBuilderProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState(toReactFlowNodes(workflow.nodes));
  const [edges, setEdges, onEdgesChange] = useEdgesState(toReactFlowEdges(workflow.edges));
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
  const [workflowName, setWorkflowName] = useState(workflow.name);
  const [showNodeConfig, setShowNodeConfig] = useState(false);

  const { trigger: updateWorkflow, isMutating: saving } = useUpdateWorkflow(workflow.id);
  const { trigger: runWorkflow, isMutating: running } = useRunWorkflow(workflow.id);

  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            style: defaultEdgeStyle,
            markerEnd: { type: MarkerType.ArrowClosed, color: "#1e1e24" },
            animated: false,
          },
          eds
        )
      ),
    [setEdges]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      if (!rfInstance || !reactFlowWrapper.current) return;

      const nodeType = event.dataTransfer.getData("application/reactflow") as NodeType;
      if (!nodeType) return;

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = rfInstance.project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newNode = {
        id: generateId(),
        type: nodeType,
        position,
        data: {
          label: nodeType.charAt(0).toUpperCase() + nodeType.slice(1),
          nodeType,
        } as WorkflowNodeData,
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [rfInstance, setNodes]
  );

  const onDragStart = useCallback((event: React.DragEvent, nodeType: NodeType) => {
    event.dataTransfer.setData("application/reactflow", nodeType);
    event.dataTransfer.effectAllowed = "move";
  }, []);

  const handleSave = async () => {
    try {
      const flowNodes: WorkflowNode[] = nodes.map((n) => ({
        id: n.id,
        type: n.type as NodeType,
        position: n.position,
        data: n.data as WorkflowNodeData,
      }));

      const flowEdges: WorkflowEdge[] = edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle ?? null,
        targetHandle: e.targetHandle ?? null,
        label: e.label as string | undefined,
        animated: e.animated ?? false,
      }));

      await updateWorkflow({
        name: workflowName,
        nodes: flowNodes,
        edges: flowEdges,
      });
      toast.success("Workflow saved");
    } catch {
      toast.error("Failed to save workflow");
    }
  };

  const handleRun = async () => {
    try {
      await runWorkflow();
      toast.success("Workflow started");
    } catch {
      toast.error("Failed to start workflow");
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Builder top bar */}
      <div className="flex items-center gap-3 border-b border-cortex-border bg-cortex-surface px-4 py-2 flex-shrink-0">
        <Link
          href="/workflows"
          className="flex items-center gap-1.5 text-cortex-muted hover:text-cortex-text transition-colors text-sm"
        >
          <ArrowLeft className="h-4 w-4" />
          Workflows
        </Link>
        <span className="text-cortex-border">/</span>
        <Input
          value={workflowName}
          onChange={(e) => setWorkflowName(e.target.value)}
          className="h-7 w-48 text-sm font-medium border-transparent bg-transparent hover:border-cortex-border focus:border-cortex-accent px-1"
        />
        <div className="flex-1" />
        <Button
          variant="outline"
          size="sm"
          onClick={handleSave}
          disabled={saving}
          className="h-7 text-xs"
        >
          <Save className="h-3.5 w-3.5" />
          {saving ? "Saving..." : "Save"}
        </Button>
        <Button
          size="sm"
          onClick={handleRun}
          disabled={running}
          className="h-7 text-xs"
        >
          <Play className="h-3.5 w-3.5" />
          {running ? "Running..." : "Run"}
        </Button>
      </div>

      {/* Builder layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Node Palette */}
        <div className="w-48 flex-shrink-0 border-r border-cortex-border bg-cortex-surface overflow-y-auto">
          <NodePalette onDragStart={onDragStart} />
        </div>

        {/* Canvas */}
        <div ref={reactFlowWrapper} className="flex-1 bg-cortex-bg">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setRfInstance}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes as any}
            onNodeClick={(_, node) => {
              setSelectedNode(node as unknown as WorkflowNode);
              setShowNodeConfig(true);
            }}
            fitView
            deleteKeyCode="Delete"
            defaultEdgeOptions={{
              style: defaultEdgeStyle,
            }}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={24}
              size={1}
              color="#1e1e24"
            />
            <Controls />
            <MiniMap
              nodeColor={(n) => {
                switch (n.type) {
                  case "agent": return "#6366f1";
                  case "condition": return "#f59e0b";
                  case "approval": return "#f97316";
                  default: return "#1e1e24";
                }
              }}
              maskColor="rgba(10,10,11,0.8)"
            />
          </ReactFlow>
        </div>

        {/* Node Config Panel */}
        {showNodeConfig && selectedNode && (
          <div className="w-64 flex-shrink-0 border-l border-cortex-border bg-cortex-surface overflow-y-auto">
            <div className="flex items-center justify-between px-3 py-2 border-b border-cortex-border">
              <div className="flex items-center gap-1.5">
                <Settings className="h-3.5 w-3.5 text-cortex-muted" />
                <span className="text-xs font-semibold text-cortex-text">Node Config</span>
              </div>
              <button
                onClick={() => setShowNodeConfig(false)}
                className="text-cortex-muted hover:text-cortex-text text-xs"
                aria-label="Close panel"
              >
                ×
              </button>
            </div>

            <div className="p-3 space-y-3">
              <div className="space-y-1.5">
                <Label className="text-[11px]">Label</Label>
                <Input
                  className="h-7 text-xs"
                  value={(selectedNode.data as WorkflowNodeData).label}
                  onChange={(e) => {
                    setNodes((nds) =>
                      nds.map((n) =>
                        n.id === selectedNode.id
                          ? { ...n, data: { ...n.data, label: e.target.value } }
                          : n
                      )
                    );
                  }}
                />
              </div>

              {selectedNode.type === "agent" && (
                <>
                  <div className="space-y-1.5">
                    <Label className="text-[11px]">Agent Name</Label>
                    <Input
                      className="h-7 text-xs"
                      placeholder="Agent name or ID"
                      value={(selectedNode.data as WorkflowNodeData).agentName ?? ""}
                      onChange={(e) => {
                        setNodes((nds) =>
                          nds.map((n) =>
                            n.id === selectedNode.id
                              ? { ...n, data: { ...n.data, agentName: e.target.value } }
                              : n
                          )
                        );
                      }}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label className="text-[11px]">Prompt Template</Label>
                    <Textarea
                      className="text-xs"
                      rows={4}
                      placeholder="Prompt template with {variables}..."
                      value={(selectedNode.data as WorkflowNodeData).promptTemplate ?? ""}
                      onChange={(e) => {
                        setNodes((nds) =>
                          nds.map((n) =>
                            n.id === selectedNode.id
                              ? { ...n, data: { ...n.data, promptTemplate: e.target.value } }
                              : n
                          )
                        );
                      }}
                    />
                  </div>
                </>
              )}

              {selectedNode.type === "approval" && (
                <div className="space-y-1.5">
                  <Label className="text-[11px]">Approvers (comma-separated)</Label>
                  <Input
                    className="h-7 text-xs"
                    placeholder="user1, user2"
                    value={((selectedNode.data as WorkflowNodeData).approvers ?? []).join(", ")}
                    onChange={(e) => {
                      setNodes((nds) =>
                        nds.map((n) =>
                          n.id === selectedNode.id
                            ? {
                                ...n,
                                data: {
                                  ...n.data,
                                  approvers: e.target.value
                                    .split(",")
                                    .map((s) => s.trim())
                                    .filter(Boolean),
                                },
                              }
                            : n
                        )
                      );
                    }}
                  />
                </div>
              )}

              <button
                onClick={() => {
                  setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
                  setShowNodeConfig(false);
                }}
                className="w-full rounded-md border border-cortex-error/30 bg-cortex-error/10 px-2 py-1.5 text-xs text-cortex-error hover:bg-cortex-error/20 transition-colors"
              >
                Delete Node
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

