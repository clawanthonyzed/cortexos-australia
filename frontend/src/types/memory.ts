export type MemoryType = "episodic" | "semantic" | "procedural" | "working";

export interface MemoryItem {
  id: string;
  agentId: string;
  agentName: string;
  type: MemoryType;
  key: string;
  value: string;
  embedding: number[] | null;
  relevanceScore: number | null;
  tags: string[];
  accessCount: number;
  lastAccessedAt: string | null;
  expiresAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface MemorySearchResult {
  item: MemoryItem;
  score: number;
  highlight: string;
}

export interface MemoryStats {
  totalEntries: number;
  totalSizeBytes: number;
  byType: Record<MemoryType, number>;
  byAgent: Array<{ agentId: string; agentName: string; count: number; sizeBytes: number }>;
  oldestEntryAt: string | null;
  newestEntryAt: string | null;
}

export interface GraphNode {
  id: string;
  label: string;
  type: "business" | "product" | "customer" | "campaign" | "research" | "agent" | "venture";
  properties: Record<string, unknown>;
  connections: number;
  x?: number;
  y?: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  weight: number;
}

export interface KnowledgeGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  stats: {
    nodeCount: number;
    edgeCount: number;
    lastUpdatedAt: string;
  };
}
