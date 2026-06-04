"use client";

import { useEffect, useRef, useCallback } from "react";
import { useAgentsStore } from "@/store/agents-store";
import { useSystemStore } from "@/store/system-store";
import { getAccessToken } from "@/lib/auth";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

type WsMessage =
  | { type: "agent.status_changed"; payload: { id: string; status: string; currentTask: string | null } }
  | { type: "agent.metrics_updated"; payload: { id: string; metrics: Record<string, unknown> } }
  | { type: "system.health"; payload: { overallPercent: number; apiLatencyMs: number; dbHealthy: boolean; wsHealthy: boolean; agentServiceHealthy: boolean; queueDepth: number; lastCheckedAt: string } }
  | { type: "alert"; payload: { level: "info" | "warning" | "error" | "success"; title: string; message: string } }
  | { type: "ping" };

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const MAX_RECONNECT_ATTEMPTS = 10;
  const BASE_RECONNECT_DELAY = 1000;

  const { updateAgent, setWsConnected } = useAgentsStore();
  const { setHealth, addAlert } = useSystemStore();

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      let msg: WsMessage;
      try {
        msg = JSON.parse(event.data as string) as WsMessage;
      } catch {
        return;
      }

      switch (msg.type) {
        case "agent.status_changed":
          updateAgent(msg.payload.id, {
            status: msg.payload.status as unknown as import("@/types/agent").AgentStatus,
            currentTask: msg.payload.currentTask,
          });
          break;

        case "agent.metrics_updated":
          updateAgent(msg.payload.id, {
            metrics: msg.payload.metrics as unknown as import("@/types/agent").AgentMetrics,
          });
          break;

        case "system.health":
          setHealth(msg.payload);
          break;

        case "alert":
          addAlert(msg.payload);
          break;

        case "ping":
          wsRef.current?.send(JSON.stringify({ type: "pong" }));
          break;
      }
    },
    [updateAgent, setHealth, addAlert]
  );

  const connect = useCallback(() => {
    const token = getAccessToken();
    const url = token ? `${WS_URL}/ws?token=${token}` : `${WS_URL}/ws`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setWsConnected(true);
      };

      ws.onmessage = handleMessage;

      ws.onclose = () => {
        setWsConnected(false);
        wsRef.current = null;

        if (reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay =
            BASE_RECONNECT_DELAY *
            Math.pow(2, reconnectAttemptsRef.current);
          reconnectAttemptsRef.current += 1;
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // WebSocket not available (SSR or network error)
    }
  }, [handleMessage, setWsConnected]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);
}
