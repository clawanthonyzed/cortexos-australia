"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import type { GraphNode, GraphEdge, KnowledgeGraph } from "@/types/memory";
import { Search, X, ZoomIn, ZoomOut } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const NODE_COLORS: Record<GraphNode["type"], string> = {
  business: "#6366f1",
  product: "#22c55e",
  customer: "#f59e0b",
  campaign: "#ec4899",
  research: "#8b5cf6",
  agent: "#06b6d4",
  venture: "#f97316",
};

interface GraphCanvasProps {
  data: KnowledgeGraph;
  isLoading?: boolean;
}

export function GraphCanvas({ data, isLoading }: GraphCanvasProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [search, setSearch] = useState("");
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());

  const containerRef = useRef<HTMLDivElement>(null);

  // Handle search highlighting
  useEffect(() => {
    if (!search) {
      setHighlightedIds(new Set());
      return;
    }
    const q = search.toLowerCase();
    const matched = new Set(
      data.nodes
        .filter(
          (n) =>
            n.label.toLowerCase().includes(q) ||
            n.type.toLowerCase().includes(q)
        )
        .map((n) => n.id)
    );
    setHighlightedIds(matched);
  }, [search, data.nodes]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-cortex-accent border-t-transparent mx-auto mb-2" />
          <p className="text-sm text-cortex-muted">Building knowledge graph...</p>
        </div>
      </div>
    );
  }

  // Simple force-layout simulation using a grid layout for SSR safety
  const width = 900;
  const height = 600;
  const nodeRadius = 18;

  // Position nodes in a circular layout
  const positionedNodes = data.nodes.map((node, idx) => {
    if (node.x !== undefined && node.y !== undefined) {
      return { ...node, px: node.x, py: node.y };
    }
    const total = data.nodes.length;
    const angle = (2 * Math.PI * idx) / total - Math.PI / 2;
    const radius = Math.min(width, height) * 0.35;
    return {
      ...node,
      px: width / 2 + radius * Math.cos(angle),
      py: height / 2 + radius * Math.sin(angle),
    };
  });

  const nodeById = new Map(positionedNodes.map((n) => [n.id, n]));

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main graph */}
      <div className="relative flex-1 overflow-hidden" ref={containerRef}>
        {/* Search bar */}
        <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-cortex-muted" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search nodes..."
              className="pl-8 h-8 w-48 text-xs bg-cortex-surface/90 backdrop-blur-sm"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-cortex-muted hover:text-cortex-text"
                aria-label="Clear search"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
          {search && (
            <span className="text-xs text-cortex-muted bg-cortex-surface/90 backdrop-blur-sm px-2 py-1 rounded-md border border-cortex-border">
              {highlightedIds.size} matches
            </span>
          )}
        </div>

        {/* Legend */}
        <div className="absolute bottom-3 left-3 z-10 flex flex-wrap gap-2 max-w-xs">
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <div key={type} className="flex items-center gap-1 bg-cortex-surface/90 backdrop-blur-sm rounded px-1.5 py-0.5 border border-cortex-border">
              <span
                className="h-2 w-2 rounded-full flex-shrink-0"
                style={{ background: color }}
              />
              <span className="text-[10px] text-cortex-muted capitalize">{type}</span>
            </div>
          ))}
        </div>

        {/* SVG graph */}
        <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="bg-cortex-bg">
          {/* Grid background */}
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e1e24" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Edges */}
          <g>
            {data.edges.map((edge) => {
              const src = nodeById.get(edge.source);
              const tgt = nodeById.get(edge.target);
              if (!src || !tgt) return null;

              const isHighlighted =
                highlightedIds.size === 0 ||
                highlightedIds.has(edge.source) ||
                highlightedIds.has(edge.target);

              return (
                <g key={edge.id}>
                  <line
                    x1={src.px}
                    y1={src.py}
                    x2={tgt.px}
                    y2={tgt.py}
                    stroke={isHighlighted ? "#2a2a36" : "#1a1a22"}
                    strokeWidth={Math.max(0.5, edge.weight ?? 1)}
                    opacity={isHighlighted ? 0.8 : 0.2}
                  />
                  {edge.label && (
                    <text
                      x={(src.px + tgt.px) / 2}
                      y={(src.py + tgt.py) / 2}
                      textAnchor="middle"
                      fill="#6b6b80"
                      fontSize="9"
                      dy={-4}
                    >
                      {edge.label}
                    </text>
                  )}
                </g>
              );
            })}
          </g>

          {/* Nodes */}
          <g>
            {positionedNodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const isHighlighted =
                highlightedIds.size === 0 || highlightedIds.has(node.id);
              const color = NODE_COLORS[node.type] ?? "#6366f1";

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.px}, ${node.py})`}
                  className="cursor-pointer"
                  onClick={() => setSelectedNode(isSelected ? null : node as GraphNode)}
                >
                  {isSelected && (
                    <circle
                      r={nodeRadius + 6}
                      fill="none"
                      stroke={color}
                      strokeWidth={2}
                      opacity={0.4}
                      className="animate-ping-slow"
                    />
                  )}
                  <circle
                    r={nodeRadius}
                    fill={color}
                    fillOpacity={isHighlighted ? 0.2 : 0.05}
                    stroke={color}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                    strokeOpacity={isHighlighted ? 1 : 0.2}
                  />
                  <text
                    textAnchor="middle"
                    dy="0.35em"
                    fill={isHighlighted ? "#e4e4f0" : "#3a3a4a"}
                    fontSize="10"
                    fontWeight={isSelected ? "700" : "500"}
                    fontFamily="Inter, sans-serif"
                  >
                    {node.label.length > 12 ? node.label.slice(0, 10) + "…" : node.label}
                  </text>
                  <text
                    y={nodeRadius + 12}
                    textAnchor="middle"
                    fill={isHighlighted ? "#6b6b80" : "#2a2a3a"}
                    fontSize="8"
                    fontFamily="Inter, sans-serif"
                  >
                    {node.type}
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {/* Detail panel */}
      {selectedNode && (
        <div className="w-64 flex-shrink-0 border-l border-cortex-border bg-cortex-surface overflow-y-auto">
          <div className="flex items-center justify-between px-3 py-2 border-b border-cortex-border">
            <span className="text-xs font-semibold text-cortex-text">Node Detail</span>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-cortex-muted hover:text-cortex-text"
              aria-label="Close detail panel"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="p-3 space-y-3">
            <div>
              <div
                className="h-10 w-10 rounded-full mb-2 flex items-center justify-center"
                style={{ background: `${NODE_COLORS[selectedNode.type]}30`, border: `1.5px solid ${NODE_COLORS[selectedNode.type]}` }}
              >
                <span className="text-sm font-bold" style={{ color: NODE_COLORS[selectedNode.type] }}>
                  {selectedNode.label[0]?.toUpperCase()}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-cortex-text">{selectedNode.label}</h3>
              <Badge
                variant="muted"
                style={{
                  color: NODE_COLORS[selectedNode.type],
                  background: `${NODE_COLORS[selectedNode.type]}15`,
                  borderColor: `${NODE_COLORS[selectedNode.type]}30`
                }}
                className="mt-1 text-[10px]"
              >
                {selectedNode.type}
              </Badge>
            </div>

            <div>
              <p className="text-[11px] font-medium uppercase tracking-wider text-cortex-muted mb-1.5">Connections</p>
              <p className="text-2xl font-bold font-mono text-cortex-text">{selectedNode.connections}</p>
            </div>

            {Object.keys(selectedNode.properties).length > 0 && (
              <div>
                <p className="text-[11px] font-medium uppercase tracking-wider text-cortex-muted mb-1.5">Properties</p>
                <div className="space-y-1.5">
                  {Object.entries(selectedNode.properties).slice(0, 8).map(([k, v]) => (
                    <div key={k} className="flex justify-between gap-2 text-xs">
                      <span className="text-cortex-muted font-mono truncate">{k}</span>
                      <span className="text-cortex-text truncate max-w-[120px]">
                        {typeof v === "object" ? JSON.stringify(v) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
