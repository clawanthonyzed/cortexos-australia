"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import type { ModelCostBreakdown } from "@/types/finance";
import { formatCurrency, formatTokens } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface CostTrackerProps {
  data: ModelCostBreakdown[];
  isLoading?: boolean;
}

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899"];

function CustomTooltip({ active, payload }: { active?: boolean; payload?: Array<{ payload: ModelCostBreakdown }> }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="rounded-lg border border-cortex-border bg-cortex-surface px-3 py-2 shadow-xl">
      <p className="text-xs font-medium text-cortex-text mb-1">{d.model}</p>
      <p className="text-xs text-cortex-muted">{formatCurrency(d.costUsd, "USD")} · {formatTokens(d.tokensUsed)} tokens</p>
      <p className="text-[11px] text-cortex-muted">{d.percentOfTotal.toFixed(1)}% of total spend</p>
    </div>
  );
}

export function CostTracker({ data, isLoading }: CostTrackerProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-[120px] w-[120px] rounded-full mx-auto" />
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <Skeleton className="h-2 w-2 rounded-full" />
            <Skeleton className="h-3 flex-1" />
            <Skeleton className="h-3 w-12" />
          </div>
        ))}
      </div>
    );
  }

  const totalCost = data.reduce((sum, d) => sum + d.costUsd, 0);

  return (
    <div>
      <div className="flex justify-center mb-3">
        <div className="relative">
          <ResponsiveContainer width={120} height={120}>
            <PieChart>
              <Pie
                data={data}
                cx={55}
                cy={55}
                innerRadius={38}
                outerRadius={55}
                dataKey="costUsd"
                strokeWidth={0}
              >
                {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-sm font-bold font-mono text-cortex-text">
              {formatCurrency(totalCost, "USD", true)}
            </span>
            <span className="text-[10px] text-cortex-muted">total</span>
          </div>
        </div>
      </div>

      <div className="space-y-1.5">
        {data.slice(0, 5).map((item, idx) => (
          <div key={item.model} className="flex items-center gap-2">
            <span
              className="h-2 w-2 flex-shrink-0 rounded-full"
              style={{ background: COLORS[idx % COLORS.length] }}
            />
            <span className="flex-1 text-xs text-cortex-muted truncate">{item.model}</span>
            <span className="font-mono text-xs text-cortex-text">
              {formatCurrency(item.costUsd, "USD", true)}
            </span>
            <span className="font-mono text-[10px] text-cortex-muted w-8 text-right">
              {item.percentOfTotal.toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
