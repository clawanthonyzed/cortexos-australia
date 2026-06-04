"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { format, parseISO } from "date-fns";
import type { RevenueDataPoint } from "@/types/finance";
import { formatCurrency } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface RevenueChartProps {
  data: RevenueDataPoint[];
  isLoading?: boolean;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-cortex-border bg-cortex-surface px-3 py-2 shadow-xl">
      <p className="mb-2 text-xs text-cortex-muted">
        {label ? format(parseISO(label), "MMM d, yyyy") : ""}
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2 text-xs">
          <span
            className="h-2 w-2 rounded-full flex-shrink-0"
            style={{ background: entry.color }}
          />
          <span className="text-cortex-muted capitalize">{entry.name}:</span>
          <span className="font-mono font-medium text-cortex-text">
            {formatCurrency(entry.value, entry.name === "costs" ? "USD" : "AUD")}
          </span>
        </div>
      ))}
    </div>
  );
}

export function RevenueChart({ data, isLoading }: RevenueChartProps) {
  if (isLoading) {
    return (
      <div className="h-[220px] flex items-end gap-1 px-2">
        {Array.from({ length: 30 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-sm"
            style={{ height: `${20 + Math.random() * 80}%` }}
          />
        ))}
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="costsGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e24" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "#6b6b80", fontSize: 10, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: string) => format(parseISO(v), "d MMM")}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fill: "#6b6b80", fontSize: 10, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `$${v >= 1000 ? `${(v / 1000).toFixed(0)}k` : v}`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="revenue"
          name="revenue"
          stroke="#6366f1"
          strokeWidth={2}
          fill="url(#revenueGradient)"
          dot={false}
          activeDot={{ r: 4, fill: "#6366f1", strokeWidth: 0 }}
        />
        <Area
          type="monotone"
          dataKey="costs"
          name="costs"
          stroke="#f59e0b"
          strokeWidth={1.5}
          fill="url(#costsGradient)"
          dot={false}
          activeDot={{ r: 3, fill: "#f59e0b", strokeWidth: 0 }}
          strokeDasharray="4 2"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
