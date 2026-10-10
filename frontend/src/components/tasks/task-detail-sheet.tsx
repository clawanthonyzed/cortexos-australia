"use client";

import { useState } from "react";
import { CheckCircle2, Circle, Loader2, MessageSquarePlus, User } from "lucide-react";
import { mutate } from "swr";
import { toast } from "sonner";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useTask } from "@/hooks/use-tasks";
import { apiClient } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import type { Task } from "@/types/task";

interface TaskComment {
  text: string;
  author?: string;
  at?: string;
}

/** Task detail drawer (2026-10-10): description, owner, tick done/reopen, notes saved to the DB. */
export function TaskDetailSheet({ task, onClose }: { task: Task | null; onClose: () => void }) {
  const { data: full } = useTask(task?.id ?? null, { refreshInterval: 0 });
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<"status" | "note" | null>(null);

  const current = full ?? task;
  const done = current?.status === "completed";
  const running = current?.status === "running" || current?.status === "retrying";
  const comments = ((full?.input as { comments?: TaskComment[] } | undefined)?.comments ?? []).slice().reverse();
  const venture = task?.title.match(/^\[([^\]]+)\]/)?.[1];

  const refresh = async () => {
    if (!task) return;
    await mutate(`/tasks/${task.id}`);
    await mutate((key: unknown) => typeof key === "string" && key.startsWith("/tasks?"));
  };

  const toggleDone = async () => {
    if (!task) return;
    setBusy("status");
    try {
      await apiClient.post(`/tasks/${task.id}/status`, { status: done ? "pending" : "completed" });
      await refresh();
      toast.success(done ? "Task reopened" : "Task marked done");
    } catch {
      toast.error("Couldn't update the task. Try again.");
    } finally {
      setBusy(null);
    }
  };

  const addNote = async () => {
    if (!task || !note.trim()) return;
    setBusy("note");
    try {
      await apiClient.post(`/tasks/${task.id}/comments`, { text: note.trim() });
      setNote("");
      await refresh();
      toast.success("Note saved");
    } catch {
      toast.error("Couldn't save the note. Try again.");
    } finally {
      setBusy(null);
    }
  };

  return (
    <Sheet open={!!task} onOpenChange={(o) => !o && onClose()}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
        {current && (
          <div className="flex flex-col gap-5">
            <SheetHeader>
              {venture && <Badge variant="muted" className="w-fit">{venture}</Badge>}
              <SheetTitle className={done ? "line-through text-cortex-muted" : ""}>
                {current.title.replace(/^\[[^\]]+\]\s*/, "")}
              </SheetTitle>
              <SheetDescription className="flex items-center gap-1.5">
                <User className="h-3.5 w-3.5" /> {task?.agentName ?? "Unassigned"} · created {formatRelativeTime(current.createdAt)}
              </SheetDescription>
            </SheetHeader>

            <div className="flex items-center gap-3">
              <Button onClick={toggleDone} disabled={busy !== null || running} variant={done ? "outline" : "default"}>
                {busy === "status" ? <Loader2 className="h-4 w-4 animate-spin" /> : done ? <Circle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
                {done ? "Reopen task" : "Mark as done"}
              </Button>
              <Badge variant={done ? "secondary" : "muted"} className="capitalize">{current.status}</Badge>
              {running && <span className="text-xs text-cortex-muted">Running tasks can't be ticked off</span>}
            </div>

            {full?.description ? (
              <div className="space-y-1">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Details</h3>
                <p className="text-sm leading-relaxed text-cortex-text whitespace-pre-wrap">{full.description}</p>
              </div>
            ) : null}

            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Notes ({comments.length})</h3>
              <Textarea
                id="task-note"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Add a note or update…"
                rows={3}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) addNote();
                }}
              />
              <Button size="sm" variant="outline" onClick={addNote} disabled={busy !== null || !note.trim()}>
                {busy === "note" ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <MessageSquarePlus className="h-3.5 w-3.5" />}
                Save note
              </Button>
              <ul className="space-y-2 pt-1">
                {comments.map((c, i) => (
                  <li key={i} className="rounded-md border border-cortex-border bg-cortex-surface/60 px-3 py-2">
                    <p className="text-sm text-cortex-text whitespace-pre-wrap">{c.text}</p>
                    <p className="text-[11px] text-cortex-muted mt-1">
                      {c.author ?? "anthony"}{c.at ? ` · ${formatRelativeTime(c.at)}` : ""}
                    </p>
                  </li>
                ))}
                {comments.length === 0 && <li className="text-xs text-cortex-muted">No notes yet.</li>}
              </ul>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
