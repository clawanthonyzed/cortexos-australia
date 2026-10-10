"use client";

import { useState } from "react";
import useSWR, { mutate } from "swr";
import { Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { apiClient, fetcher } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

interface AssetClass { key: string; label: string; icon: string; holdings: number; valued: number; total_aud: number | null }
interface Holding {
  id: string; asset_class: string; name: string; institution: string | null; owner: string | null;
  purchase_value_aud: number | null; current_estimate_aud: number | null; as_of: string | null; notes: string | null;
}
interface Ledger { net_worth_aud: number | null; classes_with_values: number; classes: AssetClass[]; holdings: Holding[]; owners: string[] }

const KEY = "/finance/assets";
const empty = { asset_class: "property", name: "", institution: "", owner: "", purchase_value_aud: "", current_estimate_aud: "", as_of: "", notes: "" };

/** Personal wealth: 8 asset classes and net worth (2026-10-10, Theodore + Tally). Values are entered by Anthony only. */
export function AssetLedger() {
  const { data, isLoading } = useSWR<Ledger>(KEY, fetcher);
  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>(empty);
  const [saving, setSaving] = useState(false);
  const [classFilter, setClassFilter] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const startAdd = (cls?: string) => {
    setEditId(null);
    setForm({ ...empty, asset_class: cls ?? "property" });
    setOpen(true);
  };
  const startEdit = (h: Holding) => {
    setEditId(h.id);
    setForm({
      asset_class: h.asset_class, name: h.name, institution: h.institution ?? "", owner: h.owner ?? "",
      purchase_value_aud: h.purchase_value_aud?.toString() ?? "", current_estimate_aud: h.current_estimate_aud?.toString() ?? "",
      as_of: h.as_of ?? "", notes: h.notes ?? "",
    });
    setOpen(true);
  };
  const num = (v: string) => (v.trim() === "" ? null : Number(v.replace(/[$,\s]/g, "")));
  const save = async () => {
    setSaving(true);
    try {
      const body = { ...form, institution: form.institution || null, owner: form.owner || null, notes: form.notes || null,
        as_of: form.as_of || null, purchase_value_aud: num(form.purchase_value_aud), current_estimate_aud: num(form.current_estimate_aud) };
      if (editId) await apiClient.put(`${KEY}/${editId}`, body);
      else await apiClient.post(KEY, body);
      await mutate(KEY);
      setOpen(false);
      toast.success("Saved");
    } catch {
      toast.error("Couldn't save. Check the amounts are plain numbers.");
    } finally {
      setSaving(false);
    }
  };
  const remove = async (h: Holding) => {
    try {
      await apiClient.delete(`${KEY}/${h.id}`);
      await mutate(KEY);
      toast.success(`Removed ${h.name}`);
    } catch {
      toast.error("Couldn't remove it");
    }
  };

  return (
    <div className="cortex-card">
      <div className="section-header">
        <div>
          <h2 className="text-sm font-semibold text-cortex-text">Personal wealth: assets &amp; net worth</h2>
          <p className="text-xs text-cortex-muted mt-0.5">Your own figures only. Nothing here is estimated by an agent.</p>
        </div>
        <Button size="sm" variant="outline" onClick={() => startAdd(classFilter ?? undefined)}><Plus className="h-3.5 w-3.5" /> Add holding</Button>
      </div>

      {isLoading || !data ? (
        <Skeleton className="h-48 w-full" />
      ) : (
        <>
          <div className="mb-4 flex flex-wrap items-baseline gap-3">
            <span className="text-xs uppercase tracking-wider text-cortex-muted">Net worth (entered)</span>
            <span className="font-mono text-2xl text-cortex-text tabular-nums">
              {data.net_worth_aud === null ? "Not entered yet" : formatCurrency(data.net_worth_aud, "AUD")}
            </span>
            <span className="text-xs text-cortex-muted">{data.classes_with_values} of 8 classes have values</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {data.classes.map((c) => (
              <button key={c.key} onClick={() => (c.holdings ? (setClassFilter(classFilter === c.key ? null : c.key), setShowAll(false)) : startAdd(c.key))}
                      aria-pressed={classFilter === c.key}
                      className={`rounded-lg border p-3 text-left transition-colors ${classFilter === c.key ? "border-cortex-accent bg-cortex-accent/10" : "border-cortex-border bg-cortex-bg/40 hover:border-cortex-accent/50"}`}>
                <p className="text-xs text-cortex-muted">{c.icon} {c.label}</p>
                <p className="mt-1 font-mono text-sm text-cortex-text tabular-nums">
                  {c.total_aud === null ? "—" : formatCurrency(c.total_aud, "AUD")}
                </p>
                <p className="text-[11px] text-cortex-muted">{c.holdings ? `${c.holdings} holding${c.holdings > 1 ? "s" : ""} · tap to view` : "Tap to add"}</p>
              </button>
            ))}
          </div>
          {data.holdings.length > 0 && (() => {
            const list = data.holdings.filter((h) => !classFilter || h.asset_class === classFilter)
              .slice().sort((a, b) => (b.current_estimate_aud ?? 0) - (a.current_estimate_aud ?? 0));
            const shown = showAll ? list : list.slice(0, 10);
            return (<>
            <div className="mt-4 flex items-center justify-between text-xs text-cortex-muted">
              <span>{classFilter ? `${data.classes.find((c) => c.key === classFilter)?.label} · ${list.length} holdings` : `All holdings · ${list.length}`} · highest value first</span>
              {classFilter && <button className="text-cortex-accent hover:underline" onClick={() => setClassFilter(null)}>Show all classes</button>}
            </div>
            <div className="mt-2 overflow-x-auto rounded-lg border border-cortex-border">
              <table className="w-full text-sm">
                <thead className="bg-cortex-bg/30 text-xs uppercase tracking-wider text-cortex-muted">
                  <tr><th className="px-3 py-2 text-left">Holding</th><th className="px-3 py-2 text-left">Owner</th>
                    <th className="px-3 py-2 text-right">Bought</th><th className="px-3 py-2 text-right">Now</th><th /></tr>
                </thead>
                <tbody className="divide-y divide-cortex-border">
                  {shown.map((h) => (
                    <tr key={h.id}>
                      <td className="px-3 py-2 text-cortex-text">{h.name}<span className="block text-xs text-cortex-muted">{h.institution ?? ""}</span></td>
                      <td className="px-3 py-2 text-xs text-cortex-muted">{h.owner ?? "—"}</td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums">{h.purchase_value_aud === null ? "—" : formatCurrency(h.purchase_value_aud, "AUD")}</td>
                      <td className="px-3 py-2 text-right font-mono tabular-nums">{h.current_estimate_aud === null ? "—" : formatCurrency(h.current_estimate_aud, "AUD")}</td>
                      <td className="px-3 py-2 text-right whitespace-nowrap">
                        <button onClick={() => startEdit(h)} aria-label={`Edit ${h.name}`} className="p-1 text-cortex-muted hover:text-cortex-text"><Pencil className="h-3.5 w-3.5" /></button>
                        <button onClick={() => remove(h)} aria-label={`Remove ${h.name}`} className="p-1 text-cortex-muted hover:text-cortex-error"><Trash2 className="h-3.5 w-3.5" /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {list.length > 10 && (
              <button onClick={() => setShowAll(!showAll)} className="mt-2 text-xs text-cortex-accent hover:underline">
                {showAll ? "Show top 10" : `Show all ${list.length}`}
              </button>
            )}
            </>);
          })()}
        </>
      )}

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editId ? "Edit holding" : "Add a holding"}</DialogTitle>
            <DialogDescription>Amounts in AUD. Leave anything blank you don&apos;t know yet.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-2.5">
            <Select value={form.asset_class} onValueChange={(v) => set("asset_class", v)}>
              <SelectTrigger aria-label="Asset class"><SelectValue /></SelectTrigger>
              <SelectContent>{data?.classes.map((c) => <SelectItem key={c.key} value={c.key}>{c.icon} {c.label}</SelectItem>)}</SelectContent>
            </Select>
            <Input id="asset-name" placeholder="Name, e.g. Withers unit" value={form.name} onChange={(e) => set("name", e.target.value)} />
            <Input id="asset-inst" placeholder="Institution / platform (optional)" value={form.institution} onChange={(e) => set("institution", e.target.value)} />
            <Select value={form.owner || undefined} onValueChange={(v) => set("owner", v)}>
              <SelectTrigger aria-label="Owned by"><SelectValue placeholder="Owned by (tax structure)" /></SelectTrigger>
              <SelectContent>{data?.owners.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent>
            </Select>
            <div className="grid grid-cols-2 gap-2">
              <Input id="asset-buy" inputMode="decimal" placeholder="Purchase value" value={form.purchase_value_aud} onChange={(e) => set("purchase_value_aud", e.target.value)} />
              <Input id="asset-now" inputMode="decimal" placeholder="Current estimate" value={form.current_estimate_aud} onChange={(e) => set("current_estimate_aud", e.target.value)} />
            </div>
            <Input id="asset-asof" type="date" aria-label="Value as of" value={form.as_of} onChange={(e) => set("as_of", e.target.value)} />
            <Textarea id="asset-notes" rows={2} placeholder="Notes (optional)" value={form.notes} onChange={(e) => set("notes", e.target.value)} />
            <div className="flex justify-end gap-2 pt-1">
              <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button onClick={save} disabled={saving || !form.name.trim()}>Save</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
