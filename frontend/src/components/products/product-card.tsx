"use client";

import { Package, ExternalLink, TrendingUp, TrendingDown } from "lucide-react";
import type { Product } from "@/types/product";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, getDelta, formatPercent } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface ProductCardProps {
  product: Product;
}

const statusVariant = {
  active: "success" as const,
  draft: "muted" as const,
  paused: "warning" as const,
  archived: "muted" as const,
};

const platformColors: Record<string, string> = {
  gumroad: "text-pink-400",
  lemonsqueezy: "text-yellow-400",
  etsy: "text-orange-400",
  shopify: "text-green-400",
  direct: "text-cortex-accent",
};

export function ProductCard({ product }: ProductCardProps) {
  const monthlyDelta = getDelta(product.revenueThisMonth, product.revenueThisMonth / 1.2); // Mock
  const isPositive = monthlyDelta >= 0;

  return (
    <div className="rounded-lg border border-cortex-border bg-cortex-surface p-4 hover:border-cortex-accent/30 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-cortex-border overflow-hidden">
            {product.imageUrl ? (
              <img src={product.imageUrl} alt={product.name} className="h-full w-full object-cover" />
            ) : (
              <Package className="h-4 w-4 text-cortex-muted" />
            )}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-cortex-text truncate">{product.name}</p>
            <p className={cn("text-[11px] font-medium capitalize", platformColors[product.platform])}>
              {product.platform}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-shrink-0 ml-2">
          <Badge variant={statusVariant[product.status]} className="text-[10px] py-0 px-1.5">
            {product.status}
          </Badge>
          {product.platformUrl && (
            <a
              href={product.platformUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-cortex-muted hover:text-cortex-accent transition-colors"
              aria-label="Open product on platform"
            >
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          )}
        </div>
      </div>

      {/* Revenue */}
      <div className="grid grid-cols-2 gap-2 mb-3">
        <div className="rounded-md bg-cortex-border/30 px-2.5 py-2">
          <p className="text-[10px] uppercase tracking-wider text-cortex-muted mb-0.5">This Month</p>
          <p className="text-sm font-bold font-mono text-cortex-text">
            {formatCurrency(product.revenueThisMonth, "AUD", true)}
          </p>
          <div className={cn("flex items-center gap-0.5 text-[10px] font-medium", isPositive ? "text-cortex-success" : "text-cortex-error")}>
            {isPositive ? <TrendingUp className="h-2.5 w-2.5" /> : <TrendingDown className="h-2.5 w-2.5" />}
            {formatPercent(Math.abs(monthlyDelta), 0)}
          </div>
        </div>
        <div className="rounded-md bg-cortex-border/30 px-2.5 py-2">
          <p className="text-[10px] uppercase tracking-wider text-cortex-muted mb-0.5">All Time</p>
          <p className="text-sm font-bold font-mono text-cortex-text">
            {formatCurrency(product.totalRevenue, "AUD", true)}
          </p>
          <p className="text-[10px] text-cortex-muted">{product.totalUnits} units</p>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs text-cortex-muted pt-2 border-t border-cortex-border">
        <span>{formatCurrency(product.priceAud, "AUD")} per unit</span>
        {product.rating && (
          <span>★ {product.rating.toFixed(1)} ({product.reviewCount})</span>
        )}
      </div>
    </div>
  );
}
