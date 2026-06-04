"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ModelCostBreakdown } from "@/types/finance";
import { formatCurrency, formatTokens } from "@/lib/utils";

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

interface CostBreakdownProps {
  data: ModelCostBreakdown[];
}

function CustomTooltip({ active, payload }: {
  active?: boolean;
  payload?: Array<{ payload: ModelCostBreakdown }>;
}) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-cortex-border bg-cortex-surface px-3 py-2 shadow-xl">
      <p className="text-xs font-medium text-cortex-text mb-1">{d.model}</p>
      <p className="text-xs text-cortex-muted">{d.provider}</p>
      <p className="text-xs font-mono text-cortex-text">{formatCurrency(d.costUsd, "USD")}</p>
      <p className="text-[11px] text-cortex-muted">{formatTokens(d.tokensUsed)} tokens · {d.requestCount} requests</p>
    </div>
  );
}

export function CostBreakdown({ data }: CostBreakdownProps) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 0, right: 16, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e24" horizontal={false} />
        <XAxis
          type="number"
          tick={{ fill: "#6b6b80", fontSize: 10, fontFamily: "monospace" }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: number) => `$${v.toFixed(2)}`}
        />
        <YAxis
          type="category"
          dataKey="model"
          tick={{ fill: "#6b6b80", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          width={120}
        />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="costUsd" radius={[0, 4, 4, 0]}>
          {data.map((_, idx) => (
            <Cell key={idx} fill={COLORS[idx % COLORS.length]} fillOpacity={0.85} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
