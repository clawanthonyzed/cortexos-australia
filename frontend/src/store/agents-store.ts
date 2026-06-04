import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import type { Agent, AgentStatus } from "@/types/agent";

interface AgentsState {
  agents: Agent[];
  selectedAgentId: string | null;
  filter: {
    status: AgentStatus | "all";
    search: string;
    venture: string | "all";
  };
  wsConnected: boolean;

  setAgents: (agents: Agent[]) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  addAgent: (agent: Agent) => void;
  removeAgent: (id: string) => void;
  setSelectedAgent: (id: string | null) => void;
  setFilter: (filter: Partial<AgentsState["filter"]>) => void;
  setWsConnected: (connected: boolean) => void;

  // Derived
  getFilteredAgents: () => Agent[];
  getAgentById: (id: string) => Agent | undefined;
  getActiveCount: () => number;
}

export const useAgentsStore = create<AgentsState>()(
  subscribeWithSelector((set, get) => ({
    agents: [],
    selectedAgentId: null,
    filter: {
      status: "all",
      search: "",
      venture: "all",
    },
    wsConnected: false,

    setAgents: (agents) => set({ agents }),

    updateAgent: (id, updates) =>
      set((state) => ({
        agents: state.agents.map((a) =>
          a.id === id ? { ...a, ...updates } : a
        ),
      })),

    addAgent: (agent) =>
      set((state) => ({ agents: [...state.agents, agent] })),

    removeAgent: (id) =>
      set((state) => ({
        agents: state.agents.filter((a) => a.id !== id),
        selectedAgentId:
          state.selectedAgentId === id ? null : state.selectedAgentId,
      })),

    setSelectedAgent: (id) => set({ selectedAgentId: id }),

    setFilter: (filter) =>
      set((state) => ({ filter: { ...state.filter, ...filter } })),

    setWsConnected: (connected) => set({ wsConnected: connected }),

    getFilteredAgents: () => {
      const { agents, filter } = get();
      return agents.filter((agent) => {
        if (filter.status !== "all" && agent.status !== filter.status)
          return false;
        if (filter.venture !== "all" && agent.venture !== filter.venture)
          return false;
        if (filter.search) {
          const q = filter.search.toLowerCase();
          return (
            agent.name.toLowerCase().includes(q) ||
            agent.purpose.toLowerCase().includes(q) ||
            agent.tags.some((t) => t.toLowerCase().includes(q))
          );
        }
        return true;
      });
    },

    getAgentById: (id) => get().agents.find((a) => a.id === id),

    getActiveCount: () =>
      get().agents.filter((a) => a.status === "running").length,
  }))
);
