import { create } from "zustand";

export interface SystemAlert {
  id: string;
  level: "info" | "warning" | "error" | "success";
  title: string;
  message: string;
  timestamp: string;
  dismissed: boolean;
}

export interface SystemHealth {
  overallPercent: number;
  apiLatencyMs: number;
  dbHealthy: boolean;
  wsHealthy: boolean;
  agentServiceHealthy: boolean;
  queueDepth: number;
  lastCheckedAt: string;
}

interface SystemState {
  health: SystemHealth | null;
  alerts: SystemAlert[];
  sidebarCollapsed: boolean;
  commandPaletteOpen: boolean;

  setHealth: (health: SystemHealth) => void;
  addAlert: (alert: Omit<SystemAlert, "id" | "dismissed" | "timestamp">) => void;
  dismissAlert: (id: string) => void;
  clearAlerts: () => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  openCommandPalette: () => void;
  closeCommandPalette: () => void;
}

export const useSystemStore = create<SystemState>()((set) => ({
  health: null,
  alerts: [],
  sidebarCollapsed: false,
  commandPaletteOpen: false,

  setHealth: (health) => set({ health }),

  addAlert: (alert) =>
    set((state) => ({
      alerts: [
        {
          ...alert,
          id: Math.random().toString(36).substring(2, 11),
          timestamp: new Date().toISOString(),
          dismissed: false,
        },
        ...state.alerts,
      ].slice(0, 50), // Keep max 50 alerts
    })),

  dismissAlert: (id) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === id ? { ...a, dismissed: true } : a
      ),
    })),

  clearAlerts: () =>
    set((state) => ({
      alerts: state.alerts.map((a) => ({ ...a, dismissed: true })),
    })),

  toggleSidebar: () =>
    set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  openCommandPalette: () => set({ commandPaletteOpen: true }),
  closeCommandPalette: () => set({ commandPaletteOpen: false }),
}));
