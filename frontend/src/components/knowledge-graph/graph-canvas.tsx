"use client";

import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import type { GraphNode, GraphEdge, KnowledgeGraph } from "@/types/memory";
import { Search, X, Filter } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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

interface PositionedNode extends GraphNode {
  px: number;
  py: number;
  vx: number;
  vy: number;
}

interface GraphCanvasProps {
  data: KnowledgeGraph;
  isLoading?: boolean;
}

// Simple force-directed layout — run for N iterations offline
function runForceLayout(nodes: GraphNode[], edges: GraphEdge[], width: number, height: number): Map<string, { x: number; y: number }> {
  const pos = new Map<string, { x: number; y: number; vx: number; vy: number }>();
  const nodeRadius = 22;
  const padding = 60;

  // Initialize positions randomly within a circle
  nodes.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
    const r = Math.min(width, height) * 0.3;
    pos.set(n.id, {
      x: width / 2 + r * Math.cos(angle) + (Math.random() - 0.5) * 20,
      y: height / 2 + r * Math.sin(angle) + (Math.random() - 0.5) * 20,
      vx: 0,
      vy: 0,
    });
  });

  const edgeSets = new Set(edges.map((e) => `${e.source}__${e.target}`));
  const hasEdge = (a: string, b: string) => edgeSets.has(`${a}__${b}`) || edgeSets.has(`${b}__${a}`);

  const IDEAL_DIST = 120;
  const REPULSION = 2500;
  const ATTRACTION = 0.05;
  const DAMPING = 0.8;
  const ITERS = 80;

  for (let iter = 0; iter < ITERS; iter++) {
    const alpha = 1 - iter / ITERS;

    // Repulsion
    const nodeIds = Array.from(pos.keys());
    for (let i = 0; i < nodeIds.length; i++) {
      for (let j = i + 1; j < nodeIds.length; j++) {
        const a = pos.get(nodeIds[i])!;
        const b = pos.get(nodeIds[j])!;
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (REPULSION / (dist * dist)) * alpha;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        a.vx -= fx;
        a.vy -= fy;
        b.vx += fx;
        b.vy += fy;
      }
    }

    // Attraction along edges
    edges.forEach((e) => {
      const a = pos.get(e.source);
      const b = pos.get(e.target);
      if (!a || !b) return;
      const dx = b.x - a.x;
      const dy = b.y - a.y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = (dist - IDEAL_DIST) * ATTRACTION * alpha;
      const fx = (dx / dist) * force;
      const fy = (dy / dist) * force;
      a.vx += fx;
      a.vy += fy;
      b.vx -= fx;
      b.vy -= fy;
    });

    // Centre gravity
    nodeIds.forEach((id) => {
      const p = pos.get(id)!;
      p.vx += (width / 2 - p.x) * 0.002 * alpha;
      p.vy += (height / 2 - p.y) * 0.002 * alpha;
    });

    // Apply velocity + damping + clamp
    nodeIds.forEach((id) => {
      const p = pos.get(id)!;
      p.vx *= DAMPING;
      p.vy *= DAMPING;
      p.x = Math.max(padding, Math.min(width - padding, p.x + p.vx));
      p.y = Math.max(padding, Math.min(height - padding, p.y + p.vy));
    });
  }

  const result = new Map<string, { x: number; y: number }>();
  pos.forEach((v, k) => result.set(k, { x: v.x, y: v.y }));
  return result;
}

export function GraphCanvas({ data, isLoading }: GraphCanvasProps) {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [ventureFilter, setVentureFilter] = useState<string>("all");
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set());

  const width = 1000;
  const height = 650;

  // Compute unique node types for filter
  const nodeTypes = useMemo(() => {
    const types = new Set(data.nodes.map((n) => n.type));
    return Array.from(types).sort();
  }, [data.nodes]);

  // Adjacency, used by the venture filter and the search highlight
  const neighbours = useMemo(() => {
    const m = new Map<string, Set<string>>();
    for (const e of data.edges) {
      if (!m.has(e.source)) m.set(e.source, new Set());
      if (!m.has(e.target)) m.set(e.target, new Set());
      m.get(e.source)!.add(e.target);
      m.get(e.target)!.add(e.source);
    }
    return m;
  }, [data.edges]);

  const ventureOptions = useMemo(
    () => data.nodes.filter((n) => n.type === "venture").sort((a, b) => a.label.localeCompare(b.label)),
    [data.nodes]
  );

  // A venture's slice of the empire: the venture, its agents, and what those agents connect to.
  // Never walks through another venture or the Empire Hub, so the slice stays on one business.
  const ventureSlice = useMemo(() => {
    if (ventureFilter === "all") return null;
    const typeOf = new Map(data.nodes.map((n) => [n.id, n.type]));
    const keep = new Set([ventureFilter]);
    let frontier = [ventureFilter];
    for (let depth = 0; depth < 2; depth++) {
      const next: string[] = [];
      for (const id of frontier) {
        for (const nb of neighbours.get(id) ?? []) {
          const t = typeOf.get(nb);
          if (keep.has(nb) || t === "venture" || t === "business") continue;
          keep.add(nb);
          next.push(nb);
        }
      }
      frontier = next;
    }
    return keep;
  }, [ventureFilter, data.nodes, neighbours]);

  // Filter nodes by category and venture
  const visibleNodes = useMemo(() => {
    let nodes = data.nodes;
    if (ventureSlice) nodes = nodes.filter((n) => ventureSlice.has(n.id));
    if (categoryFilter !== "all") nodes = nodes.filter((n) => n.type === categoryFilter || n.id === ventureFilter);
    return nodes;
  }, [data.nodes, categoryFilter, ventureSlice, ventureFilter]);

  const visibleIds = useMemo(() => new Set(visibleNodes.map((n) => n.id)), [visibleNodes]);

  const visibleEdges = useMemo(() =>
    data.edges.filter((e) => visibleIds.has(e.source) && visibleIds.has(e.target)),
    [data.edges, visibleIds]
  );

  // Run force layout
  const positions = useMemo(
    () => runForceLayout(visibleNodes, visibleEdges, width, height),
    [visibleNodes, visibleEdges]
  );

  const positionedNodes: (GraphNode & { px: number; py: number })[] = useMemo(
    () => visibleNodes.map((n) => {
      const p = positions.get(n.id) ?? { x: width / 2, y: height / 2 };
      return { ...n, px: p.x, py: p.y };
    }),
    [visibleNodes, positions]
  );

  const nodeById = useMemo(
    () => new Map(positionedNodes.map((n) => [n.id, n])),
    [positionedNodes]
  );

  // Search highlight
  useEffect(() => {
    if (!search) {
      setHighlightedIds(new Set());
      return;
    }
    const q = search.toLowerCase();
    const direct = visibleNodes
      .filter((n) => n.label.toLowerCase().includes(q) || n.type.toLowerCase().includes(q))
      .map((n) => n.id);
    // highlight each match plus everything it is directly connected to
    const matched = new Set(direct);
    for (const id of direct) for (const nb of neighbours.get(id) ?? []) matched.add(nb);
    setHighlightedIds(matched);
  }, [search, visibleNodes, neighbours]);

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

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main graph */}
      <div className="relative flex-1 overflow-hidden">
        {/* Controls */}
        <div className="absolute top-3 left-3 z-10 flex items-center gap-2 flex-wrap">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-cortex-muted" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Find an agent..."
              className="pl-8 h-8 w-44 text-xs bg-cortex-surface/90 backdrop-blur-sm"
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
          <Select value={categoryFilter} onValueChange={setCategoryFilter}>
            <SelectTrigger className="h-8 w-36 text-xs bg-cortex-surface/90 backdrop-blur-sm">
              <Filter className="h-3 w-3 mr-1 text-cortex-muted" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {nodeTypes.map((t) => (
                <SelectItem key={t} value={t} className="capitalize">{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={ventureFilter} onValueChange={setVentureFilter}>
            <SelectTrigger className="h-8 w-48 text-xs bg-cortex-surface/90 backdrop-blur-sm" aria-label="Filter by venture">
              <SelectValue placeholder="All ventures" />
            </SelectTrigger>
            <SelectContent className="max-h-80">
              <SelectItem value="all">All ventures</SelectItem>
              {ventureOptions.map((v) => (
                <SelectItem key={v.id} value={v.id}>{v.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          {ventureFilter !== "all" && (
            <button
              onClick={() => setVentureFilter("all")}
              className="text-xs text-cortex-muted bg-cortex-surface/90 px-2 py-1 rounded-md border border-cortex-border hover:text-cortex-text"
            >
              Show whole empire
            </button>
          )}
          {search && (
            <span className="text-xs text-cortex-muted bg-cortex-surface/90 backdrop-blur-sm px-2 py-1 rounded-md border border-cortex-border">
              {highlightedIds.size} highlighted
            </span>
          )}
        </div>

        {/* Legend */}
        <div className="absolute bottom-3 left-3 z-10 flex flex-wrap gap-1.5 max-w-xs">
          {Object.entries(NODE_COLORS)
            .filter(([type]) => nodeTypes.includes(type as GraphNode["type"]))
            .map(([type, color]) => (
              <button
                key={type}
                onClick={() => setCategoryFilter(categoryFilter === type ? "all" : type)}
                className={cn(
                  "flex items-center gap-1 rounded px-1.5 py-0.5 border text-[10px] text-cortex-muted capitalize transition-colors",
                  categoryFilter === type
                    ? "border-white/30 bg-cortex-surface"
                    : "bg-cortex-surface/90 backdrop-blur-sm border-cortex-border"
                )}
              >
                <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ background: color }} />
                {type}
              </button>
            ))}
        </div>

        <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="bg-cortex-bg">
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e1e24" strokeWidth="0.5" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />

          {/* Edges */}
          <g>
            {visibleEdges.map((edge) => {
              const src = nodeById.get(edge.source);
              const tgt = nodeById.get(edge.target);
              if (!src || !tgt) return null;
              const isHighlighted = highlightedIds.size === 0 || highlightedIds.has(edge.source) || highlightedIds.has(edge.target);
              return (
                <line
                  key={edge.id}
                  x1={src.px}
                  y1={src.py}
                  x2={tgt.px}
                  y2={tgt.py}
                  stroke={isHighlighted ? "#2a2a36" : "#1a1a22"}
                  strokeWidth={Math.max(0.5, (edge.weight ?? 1) * 0.8)}
                  opacity={isHighlighted ? 0.9 : 0.2}
                />
              );
            })}
          </g>

          {/* Nodes */}
          <g>
            {positionedNodes.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const isHighlighted = highlightedIds.size === 0 || highlightedIds.has(node.id);
              const color = NODE_COLORS[node.type] ?? "#6366f1";
              const r = 16 + Math.min(node.connections, 10) * 1.5;

              return (
                <g
                  key={node.id}
                  transform={`translate(${node.px}, ${node.py})`}
                  className="cursor-pointer"
                  onClick={() => setSelectedNode(isSelected ? null : (node as GraphNode))}
                >
                  {isSelected && (
                    <circle r={r + 8} fill="none" stroke={color} strokeWidth={2} opacity={0.35} />
                  )}
                  <circle
                    r={r}
                    fill={color}
                    fillOpacity={isHighlighted ? 0.2 : 0.04}
                    stroke={color}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                    strokeOpacity={isHighlighted ? 1 : 0.2}
                  />
                  <text
                    textAnchor="middle"
                    dy="0.35em"
                    fill={isHighlighted ? "#e4e4f0" : "#3a3a4a"}
                    fontSize={node.label.length > 10 ? "8" : "9"}
                    fontWeight={isSelected ? "700" : "500"}
                    fontFamily="Inter, sans-serif"
                  >
                    {node.label.length > 14 ? node.label.slice(0, 12) + "..." : node.label}
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
              <h3 className="text-sm font-semibold text-cortex-text break-words">{selectedNode.label}</h3>
              <Badge
                variant="muted"
                style={{
                  color: NODE_COLORS[selectedNode.type],
                  background: `${NODE_COLORS[selectedNode.type]}15`,
                  borderColor: `${NODE_COLORS[selectedNode.type]}30`,
                }}
                className="mt-1 text-[10px] capitalize"
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
                  {Object.entries(selectedNode.properties).slice(0, 10).map(([k, v]) => (
                    <div key={k} className="flex flex-col gap-0.5 text-xs">
                      <span className="text-cortex-muted font-mono text-[10px]">{k}</span>
                      <span className="text-cortex-text break-words">
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
