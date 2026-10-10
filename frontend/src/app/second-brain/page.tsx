"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { BookOpen, ChevronRight, FileText, Folder, Lock, Search, X } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { fetcher } from "@/lib/api";
import { cn, formatRelativeTime } from "@/lib/utils";

interface NoteMeta {
  name: string;
  path: string;
  size: number;
  modified: string;
}
interface FolderNode {
  name: string;
  path: string;
  count: number;
  latest: string | null;
  folders: FolderNode[];
  notes: NoteMeta[];
}
interface Note extends NoteMeta {
  content: string;
}
interface SearchResult {
  path: string;
  name: string;
  snippet: string;
}

const PINNED = ["empire/CURRENT-STATE.md", "empire/PAUSED-AND-BACKLOGGED-TASKS.md", "INDEX.md"];

/** Second Brain reader (2026-10-10): browse and read the vault at /opt/openclaw/second-brain. Read-only. */
function FolderView({
  node, depth, open, toggle, selected, onSelect, filter,
}: {
  node: FolderNode; depth: number; open: Set<string>; toggle: (p: string) => void;
  selected: string | null; onSelect: (p: string) => void; filter: string;
}) {
  const f = filter.toLowerCase();
  const notes = f ? node.notes.filter((n) => n.path.toLowerCase().includes(f)) : node.notes;
  const folders = node.folders.filter((sub) => !f || JSON.stringify(sub).toLowerCase().includes(f));
  const isOpen = depth === 0 || open.has(node.path) || !!f;
  return (
    <div>
      {depth > 0 && (
        <button
          type="button"
          onClick={() => toggle(node.path)}
          aria-expanded={isOpen}
          className="flex w-full items-center gap-1.5 rounded px-2 py-1 text-left text-sm hover:bg-white/5"
          style={{ paddingLeft: 8 + (depth - 1) * 14 }}
        >
          <ChevronRight className={cn("h-3.5 w-3.5 shrink-0 text-cortex-muted transition-transform", isOpen && "rotate-90")} />
          {node.name === "private" ? <Lock className="h-3.5 w-3.5 shrink-0 text-amber-400" /> : <Folder className="h-3.5 w-3.5 shrink-0 text-cortex-muted" />}
          <span className="truncate text-cortex-text">{node.name}</span>
          <span className="ml-auto text-[11px] tabular-nums text-cortex-muted">{node.count}</span>
        </button>
      )}
      {isOpen && (
        <>
          {folders.map((sub) => (
            <FolderView key={sub.path} node={sub} depth={depth + 1} open={open} toggle={toggle}
                        selected={selected} onSelect={onSelect} filter={filter} />
          ))}
          {notes.map((n) => (
            <button
              key={n.path}
              type="button"
              onClick={() => onSelect(n.path)}
              className={cn(
                "flex w-full items-center gap-1.5 rounded px-2 py-1 text-left text-sm hover:bg-white/5",
                selected === n.path ? "bg-cortex-accent/15 text-cortex-text" : "text-cortex-muted"
              )}
              style={{ paddingLeft: 8 + depth * 14 }}
              title={n.path}
            >
              <FileText className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{n.name}</span>
            </button>
          ))}
        </>
      )}
    </div>
  );
}

export default function SecondBrainPage() {
  const { data: tree, error, isLoading } = useSWR<FolderNode>("/second-brain/tree", fetcher, { refreshInterval: 60000 });
  const [selected, setSelected] = useState<string | null>(PINNED[0]);
  const [open, setOpen] = useState<Set<string>>(new Set(["empire", "inbox"]));
  const [filter, setFilter] = useState("");
  const [query, setQuery] = useState("");
  const [submitted, setSubmitted] = useState("");
  const { data: note, error: noteError, isLoading: noteLoading } = useSWR<Note>(
    selected ? `/second-brain/note?path=${encodeURIComponent(selected)}` : null, fetcher
  );
  const { data: search, isLoading: searching } = useSWR<{ results: SearchResult[]; truncated: boolean }>(
    submitted.length >= 2 ? `/second-brain/search?q=${encodeURIComponent(submitted)}` : null, fetcher
  );
  const toggle = (p: string) =>
    setOpen((s) => {
      const n = new Set(s);
      n.has(p) ? n.delete(p) : n.add(p);
      return n;
    });
  const crumbs = useMemo(() => (selected ?? "").split("/"), [selected]);

  return (
    <AppShell>
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="page-title flex items-center gap-2"><BookOpen className="h-5 w-5" /> Second Brain</h1>
            <p className="text-sm text-cortex-muted mt-0.5">
              {tree ? `${tree.count} notes · last change ${tree.latest ? formatRelativeTime(tree.latest) : "unknown"} · read-only` : "Loading notes..."}
            </p>
          </div>
          <form
            className="relative"
            onSubmit={(e) => {
              e.preventDefault();
              setSubmitted(query.trim());
            }}
          >
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-cortex-muted" />
            <Input id="brain-search" value={query} onChange={(e) => setQuery(e.target.value)}
                   placeholder="Search inside notes, press Enter" className="pl-8 h-9 w-72 text-sm" />
          </form>
        </div>

        <div className="flex flex-wrap gap-2">
          {PINNED.map((p) => (
            <button key={p} onClick={() => setSelected(p)}
                    className={cn("rounded-full border px-3 py-1 text-xs transition-colors",
                      selected === p ? "border-cortex-accent bg-cortex-accent/15 text-cortex-text" : "border-cortex-border text-cortex-muted hover:text-cortex-text")}>
              📌 {p.split("/").pop()}
            </button>
          ))}
        </div>

        {submitted && (
          <div className="rounded-xl border border-cortex-border bg-cortex-surface">
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-cortex-border">
              <span className="text-sm text-cortex-text">
                {searching ? "Searching..." : `${search?.results.length ?? 0} notes mention "${submitted}"${search?.truncated ? " (first 50)" : ""}`}
              </span>
              <button onClick={() => { setSubmitted(""); setQuery(""); }} aria-label="Close search" className="text-cortex-muted hover:text-cortex-text">
                <X className="h-4 w-4" />
              </button>
            </div>
            <ul className="max-h-64 overflow-y-auto divide-y divide-cortex-border">
              {(search?.results ?? []).map((r) => (
                <li key={r.path}>
                  <button onClick={() => setSelected(r.path)} className="w-full px-4 py-2 text-left hover:bg-white/5">
                    <p className="text-sm text-cortex-text">{r.path}</p>
                    <p className="text-xs text-cortex-muted truncate">{r.snippet}</p>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-[320px_minmax(0,1fr)] gap-4 min-h-[70vh]">
          <aside className="rounded-xl border border-cortex-border bg-cortex-surface p-2 lg:max-h-[78vh] lg:overflow-y-auto">
            <Input id="brain-filter" value={filter} onChange={(e) => setFilter(e.target.value)}
                   placeholder="Filter by file name" className="mb-2 h-8 text-xs" />
            {error ? (
              <p className="p-3 text-sm text-cortex-error">Couldn&apos;t load the notes list. Refresh to try again.</p>
            ) : isLoading || !tree ? (
              <div className="space-y-2 p-2">{Array.from({ length: 10 }).map((_, i) => <Skeleton key={i} className="h-5 w-full" />)}</div>
            ) : (
              <FolderView node={tree} depth={0} open={open} toggle={toggle} selected={selected} onSelect={setSelected} filter={filter} />
            )}
          </aside>

          <article className="rounded-xl border border-cortex-border bg-cortex-surface p-5 md:p-8 min-w-0 lg:max-h-[78vh] lg:overflow-y-auto">
            {!selected ? (
              <p className="text-sm text-cortex-muted">Pick a note on the left.</p>
            ) : noteLoading ? (
              <div className="space-y-3"><Skeleton className="h-7 w-1/2" /><Skeleton className="h-64 w-full" /></div>
            ) : noteError || !note ? (
              <p className="text-sm text-cortex-error">This note couldn&apos;t be opened (moved, deleted, or not readable).</p>
            ) : (
              <>
                <div className="mb-4 flex flex-wrap items-center gap-2 text-xs text-cortex-muted">
                  {crumbs.map((c, i) => (
                    <span key={i} className="flex items-center gap-2">
                      {i > 0 && <ChevronRight className="h-3 w-3" />}
                      <span className={i === crumbs.length - 1 ? "text-cortex-text" : ""}>{c}</span>
                    </span>
                  ))}
                  <Badge variant="muted" className="ml-auto">updated {formatRelativeTime(note.modified)}</Badge>
                </div>
                {note.name.endsWith(".md") ? (
                  <div className="prose prose-invert prose-sm md:prose-base max-w-none prose-headings:font-semibold prose-a:text-cortex-accent prose-table:text-sm prose-pre:bg-cortex-bg prose-pre:border prose-pre:border-cortex-border prose-td:border prose-td:border-cortex-border prose-th:border prose-th:border-cortex-border prose-td:px-2 prose-th:px-2">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}
                                   components={{ a: ({ node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" /> }}>
                      {note.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <pre className="whitespace-pre-wrap text-sm text-cortex-text font-mono">{note.content}</pre>
                )}
              </>
            )}
          </article>
        </div>
      </div>
    </AppShell>
  );
}
