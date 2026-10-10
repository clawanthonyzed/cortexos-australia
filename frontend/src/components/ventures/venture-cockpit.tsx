"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import useSWR, { mutate } from "swr";
import { CheckCircle2, Clock, ExternalLink, Loader2, Play, XCircle } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiClient, fetcher } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";

interface Playbook {
  id: string;
  title: string;
  brief: string;
}
interface PlaybooksResponse {
  venture: string;
  manager: string | null;
  manager_id: string | null;
  playbooks: Playbook[];
}
interface TaskItem {
  id: string;
  title: string;
  status: string;
  created_at: string;
  deliverable?: string | null;
}

const STATUS: Record<string, { icon: React.ElementType; cls: string }> = {
  queued: { icon: Clock, cls: "text-cortex-muted" },
  pending: { icon: Clock, cls: "text-cortex-muted" },
  running: { icon: Loader2, cls: "text-cortex-accent animate-spin" },
  completed: { icon: CheckCircle2, cls: "text-cortex-success" },
  failed: { icon: XCircle, cls: "text-cortex-error" },
};

/** Venture cockpit (2026-10-10): dispatch a work order to the venture's manager through the
 * A2A hub, then watch it move queued -> running -> completed with a link to the deliverable. */
export function VentureCockpit({ slug, name }: { slug: string; name: string }) {
  const { data: pb } = useSWR<PlaybooksResponse>(`/ventures/${slug}/playbooks`, fetcher);
  const { data: tasks } = useSWR<{ items: TaskItem[] }>(
    pb?.manager_id ? `/tasks?agent_id=${pb.manager_id}&page_size=6` : null,
    fetcher,
    { refreshInterval: 3000 }
  );
  const [open, setOpen] = useState(false);
  const [choice, setChoice] = useState<string>("");
  const [title, setTitle] = useState("");
  const [brief, setBrief] = useState("");
  const [sending, setSending] = useState(false);

  useEffect(() => {
    const p = pb?.playbooks.find((x) => x.id === choice);
    if (p) {
      setTitle(p.title);
      setBrief(p.brief);
    }
  }, [choice, pb]);

  const openDialog = () => {
    if (pb?.playbooks[0]) setChoice(pb.playbooks[0].id);
    setOpen(true);
  };

  const dispatch = async () => {
    setSending(true);
    try {
      await apiClient.post(`/ventures/${slug}/dispatch`, { title, brief, playbook_id: choice });
      toast.success(`Sent to ${pb?.manager ?? "the manager"}. Watch it run below or on the Tasks tab.`);
      setOpen(false);
      await mutate((key: unknown) => typeof key === "string" && key.startsWith("/tasks"));
    } catch {
      toast.error("Couldn't dispatch the task. Check the A2A hub and try again.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="rounded-xl border border-cortex-accent/40 bg-cortex-surface overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-cortex-border">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-cortex-muted">Cockpit</p>
          <p className="text-sm text-cortex-text mt-0.5">
            Give {pb?.manager ?? "this venture's manager"} a job. It runs in the background and the result lands here.
          </p>
        </div>
        <Button onClick={openDialog} disabled={!pb?.manager}>
          <Play className="h-4 w-4" /> Run task
        </Button>
      </div>

      <ul className="divide-y divide-cortex-border">
        {(tasks?.items ?? []).map((t) => {
          const s = STATUS[t.status] ?? STATUS.queued;
          return (
            <li key={t.id} className="flex items-center gap-3 px-5 py-3">
              <s.icon className={`h-4 w-4 shrink-0 ${s.cls}`} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-cortex-text">{t.title.replace(/^\[[^\]]+\]\s*/, "")}</p>
                <p className="text-xs text-cortex-muted">
                  <span className="capitalize">{t.status}</span> · {formatRelativeTime(t.created_at)}
                </p>
              </div>
              {t.deliverable && (
                <a href={t.deliverable} target="_blank" rel="noopener noreferrer"
                   className="inline-flex items-center gap-1 text-xs text-cortex-accent hover:underline shrink-0">
                  Open result <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </li>
          );
        })}
        {tasks && tasks.items.length === 0 && (
          <li className="px-5 py-5 text-sm text-cortex-muted">No tasks yet. Press Run task to send the first one.</li>
        )}
      </ul>
      <div className="px-5 py-2.5 border-t border-cortex-border text-xs text-cortex-muted">
        Updates every 3 seconds · <Link href="/tasks" className="text-cortex-accent hover:underline">All tasks</Link>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Run a task for {name}</DialogTitle>
            <DialogDescription>
              Goes to {pb?.manager} through the A2A hub. While Anthropic credit is paused it runs as a $0 draft on free models.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <Select value={choice} onValueChange={setChoice}>
              <SelectTrigger aria-label="Choose a playbook">
                <SelectValue placeholder="Choose a playbook" />
              </SelectTrigger>
              <SelectContent>
                {pb?.playbooks.map((p) => (
                  <SelectItem key={p.id} value={p.id}>{p.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Textarea id="cockpit-brief" rows={7} value={brief} onChange={(e) => setBrief(e.target.value)} />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button onClick={dispatch} disabled={sending || !brief.trim()}>
                {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />} Dispatch
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
