"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { format, parseISO } from "date-fns";
import type { RevenueDataPoint } from "@/types/finance";
import { formatCurrency } from "@/lib/utils";

interface RevenueBreakdownProps {
  data: RevenueDataPoint[];
}

function CustomTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-cortex-border bg-cortex-surface px-3 py-2 shadow-xl">
      <p className="mb-2 text-xs font-medium text-cortex-muted">
        {label ? format(parseISO(label), "MMM d, yyyy") : ""}
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 text-xs">
          <span className="h-2 w-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-cortex-muted capitalize">{entry.name}:</span>
          <span className="font-mono font-semibold text-cortex-text">
            {formatCurrency(entry.value, entry.name === "costs" ? "USD" : "AUD")}
          </span>
        </div>
      ))}
    </div>
  );
}

export function RevenueBreakdown({ data }: RevenueBreakdownProps) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <defs>
          <linearGradient id="revenueGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="costsGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="profitGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e24" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "#6b6b80", fontSize: 10, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: string) => format(parseISO(v), "MMM d")}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: "#6b6b80", fontSize: 10, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `$${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(value) => (
            <span style={{ color: "#6b6b80", fontSize: "11px", textTransform: "capitalize" }}>
              {value}
            </span>
          )}
        />
        <Area type="monotone" dataKey="revenue" name="revenue" stroke="#6366f1" strokeWidth={2} fill="url(#revenueGrad)" dot={false} />
        <Area type="monotone" dataKey="costs" name="costs" stroke="#ef4444" strokeWidth={1.5} fill="url(#costsGrad)" dot={false} strokeDasharray="4 2" />
        <Area type="monotone" dataKey="profit" name="profit" stroke="#22c55e" strokeWidth={2} fill="url(#profitGrad)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
