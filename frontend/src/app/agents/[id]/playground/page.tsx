"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import useSWR from "swr";
import { ArrowLeft, Play, Square, Zap, Clock, DollarSign, Brain } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { fetcher, BASE_URL } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

interface AgentBrief {
  id: string;
  name: string;
  status: string;
  model_name: string;
  model_provider: string;
  purpose: string;
}

type StreamEvent =
  | { event: "started"; agent: string; task: string }
  | { event: "thinking"; message: string }
  | { event: "token"; delta: string }
  | { event: "completed"; content: string; duration_seconds: number; agent: string }
  | { event: "error"; error: string };

interface RunStats {
  durationSeconds: number;
  tokenCount: number;
}

export default function AgentPlaygroundPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const { data: agent, isLoading } = useSWR<AgentBrief>(
    `/agents/${id}`,
    fetcher
  );

  const [prompt, setPrompt] = useState("");
  const [output, setOutput] = useState("");
  const [phase, setPhase] = useState<"idle" | "running" | "done" | "error">("idle");
  const [stats, setStats] = useState<RunStats | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const outputRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const run = useCallback(async () => {
    if (!prompt.trim() || phase === "running") return;

    setOutput("");
    setStats(null);
    setErrorMsg("");
    setPhase("running");

    const ctrl = new AbortController();
    abortRef.current = ctrl;

    // Build URL — agent stream endpoint
    const token = localStorage.getItem("access_token") ?? "";
    const streamUrl = `${BASE_URL}/agents/${id}/stream?task=${encodeURIComponent(prompt)}&token=${token}`;

    try {
      const res = await fetch(streamUrl, {
        headers: { Authorization: `Bearer ${token}` },
        signal: ctrl.signal,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Stream failed" }));
        throw new Error(err.error || `HTTP ${res.status}`);
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        // Parse SSE frames
        const frames = buffer.split("\n\n");
        buffer = frames.pop() ?? "";

        for (const frame of frames) {
          const lines = frame.split("\n");
          const eventLine = lines.find((l) => l.startsWith("event:"));
          const dataLine = lines.find((l) => l.startsWith("data:"));
          if (!dataLine) continue;

          const eventType = eventLine?.replace("event:", "").trim() ?? "message";
          let data: StreamEvent;
          try {
            data = JSON.parse(dataLine.replace("data:", "").trim());
          } catch {
            continue;
          }

          if (data.event === "token") {
            setOutput((prev) => prev + data.delta);
          } else if (data.event === "thinking") {
            setOutput((prev) => prev + `\n[${data.message}]\n`);
          } else if (data.event === "completed") {
            setStats({
              durationSeconds: data.duration_seconds,
              tokenCount: 0,
            });
            setPhase("done");
          } else if (data.event === "error") {
            setErrorMsg(data.error);
            setPhase("error");
          }
        }
      }

      if (phase === "running") setPhase("done");
    } catch (err: any) {
      if (err.name === "AbortError") {
        setPhase("idle");
      } else {
        setErrorMsg(err.message ?? "Unknown error");
        setPhase("error");
      }
    }
  }, [id, prompt, phase]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setPhase("idle");
  }, []);

  const statusColors: Record<string, string> = {
    idle: "bg-cortex-muted/30 text-cortex-muted",
    running: "bg-amber-500/20 text-amber-400",
    done: "bg-cortex-success/20 text-cortex-success",
    error: "bg-red-500/20 text-red-400",
  };

  return (
    <AppShell>
      <div className="flex flex-col h-full space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push(`/agents/${id}`)}
            className="text-cortex-muted hover:text-cortex-text"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="flex-1">
            {isLoading ? (
              <Skeleton className="h-6 w-48" />
            ) : (
              <>
                <h1 className="page-title flex items-center gap-2">
                  <Zap className="h-5 w-5 text-cortex-accent" />
                  {agent?.name} — Playground
                </h1>
                <p className="text-sm text-cortex-muted mt-0.5">
                  {agent?.model_provider}/{agent?.model_name}
                </p>
              </>
            )}
          </div>
          <Badge className={statusColors[phase]}>
            {phase === "running" ? "Streaming…" : phase.charAt(0).toUpperCase() + phase.slice(1)}
          </Badge>
        </div>

        {/* Split pane */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 flex-1 min-h-0">
          {/* Input */}
          <div className="flex flex-col gap-3">
            <label className="text-xs font-semibold text-cortex-muted uppercase tracking-wider">
              Prompt
            </label>
            <Textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={`Give ${agent?.name ?? "the agent"} a task…`}
              className="flex-1 min-h-[200px] font-mono text-sm resize-none bg-cortex-surface border-cortex-border"
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) run();
              }}
              disabled={phase === "running"}
            />
            <div className="flex gap-2">
              <Button
                onClick={run}
                disabled={!prompt.trim() || phase === "running" || isLoading}
                className="flex-1"
              >
                <Play className="h-4 w-4" />
                Run  <span className="text-xs opacity-60 ml-1">⌘↵</span>
              </Button>
              {phase === "running" && (
                <Button variant="destructive" onClick={stop} className="px-4">
                  <Square className="h-4 w-4" />
                  Stop
                </Button>
              )}
            </div>

            {/* Agent info */}
            {agent && (
              <div className="rounded-lg border border-cortex-border bg-cortex-surface p-3 space-y-1.5">
                <p className="text-xs font-semibold text-cortex-muted uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Brain className="h-3.5 w-3.5" /> Agent Context
                </p>
                <p className="text-sm text-cortex-text">{agent.purpose}</p>
              </div>
            )}
          </div>

          {/* Output */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-cortex-muted uppercase tracking-wider">
                Output
              </label>
              {stats && (
                <div className="flex items-center gap-3 text-xs text-cortex-muted">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {stats.durationSeconds.toFixed(2)}s
                  </span>
                </div>
              )}
            </div>

            <div
              ref={outputRef}
              className={`flex-1 min-h-[200px] max-h-[500px] overflow-y-auto rounded-lg border font-mono text-sm p-4 whitespace-pre-wrap leading-relaxed ${
                phase === "error"
                  ? "border-red-500/30 bg-red-500/5 text-red-400"
                  : "border-cortex-border bg-cortex-surface text-cortex-text"
              }`}
            >
              {phase === "error" && errorMsg ? (
                <span className="text-red-400">Error: {errorMsg}</span>
              ) : output ? (
                output
              ) : phase === "running" ? (
                <span className="animate-pulse text-cortex-muted">Streaming…</span>
              ) : (
                <span className="text-cortex-muted">Output will appear here.</span>
              )}
            </div>

            {/* Stats bar */}
            {phase === "done" && stats && (
              <div className="flex items-center gap-4 rounded-lg border border-cortex-success/20 bg-cortex-success/5 px-4 py-2 text-sm">
                <span className="flex items-center gap-1.5 text-cortex-success font-mono">
                  <Clock className="h-3.5 w-3.5" />
                  {stats.durationSeconds.toFixed(2)}s
                </span>
                <span className="text-cortex-muted text-xs">Completed successfully</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
