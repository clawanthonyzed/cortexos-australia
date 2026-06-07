"use client";

import { useState } from "react";
import useSWR from "swr";
import { Plus, Search, Package, TrendingUp } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { ProductCard } from "@/components/products/product-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { fetcher } from "@/lib/api";
import type { Product } from "@/types/product";
import { formatCurrency } from "@/lib/utils";

interface ProductBrief {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  product_type: string;
  status: string;
  price_aud: number;
  cover_image_url: string | null;
  total_sales: number;
  total_revenue_aud: number;
  created_at: string;
  updated_at: string;
}

interface ProductsBackend {
  items: ProductBrief[];
  total: number;
  page: number;
  page_size: number;
}

interface ProductsResponse {
  products: Product[];
  total: number;
  totalRevenueAud: number;
}

function adaptProduct(b: ProductBrief): Product {
  return {
    id: b.id,
    name: b.name,
    description: b.description ?? "",
    type: (b.product_type as Product["type"]) ?? "digital_download",
    status: (b.status === "published" ? "active" : b.status) as Product["status"],
    platform: "direct",
    platformId: null,
    platformUrl: null,
    venture: null,
    priceAud: b.price_aud,
    currency: "AUD",
    totalRevenue: b.total_revenue_aud,
    totalUnits: b.total_sales,
    revenueThisMonth: 0,
    unitsThisMonth: 0,
    conversionRate: null,
    rating: null,
    reviewCount: 0,
    tags: [],
    imageUrl: b.cover_image_url,
    salesHistory: [],
    createdAt: b.created_at,
    updatedAt: b.updated_at,
  };
}

async function productsFetcher(url: string): Promise<ProductsResponse> {
  const raw = await fetcher<ProductsBackend>(url);
  const products = raw.items.map(adaptProduct);
  return {
    products,
    total: raw.total,
    totalRevenueAud: products.reduce((s, p) => s + p.totalRevenue, 0),
  };
}

export default function ProductsPage() {
  const [search, setSearch] = useState("");
  const [platform, setPlatform] = useState("all");
  const [status, setStatus] = useState("all");

  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (platform !== "all") params.set("platform", platform);
  if (status !== "all") params.set("status", status);

  const { data, isLoading } = useSWR<ProductsResponse>(
    `/products?${params.toString()}`,
    productsFetcher,
    { refreshInterval: 30000 }
  );

  const products = data?.products ?? [];

  return (
    <AppShell>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="page-title">Products</h1>
            <p className="text-sm text-cortex-muted mt-0.5">
              {isLoading
                ? "Loading..."
                : `${data?.total ?? 0} products · ${formatCurrency(data?.totalRevenueAud ?? 0, "AUD", true)} total revenue`}
            </p>
          </div>
          <Button>
            <Plus className="h-4 w-4" />
            Add Product
          </Button>
        </div>

        {/* Revenue summary */}
        {!isLoading && data && (
          <div className="flex items-center gap-2 rounded-lg border border-cortex-success/20 bg-cortex-success/5 px-4 py-3">
            <TrendingUp className="h-4 w-4 text-cortex-success flex-shrink-0" />
            <span className="text-sm text-cortex-text">
              Total product revenue:{" "}
              <span className="font-bold font-mono text-cortex-success">
                {formatCurrency(data.totalRevenueAud, "AUD")}
              </span>
            </span>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-3 flex-wrap">
          <div className="relative flex-1 min-w-[200px] max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-cortex-muted" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search products..."
              className="pl-9"
            />
          </div>
          <Select value={platform} onValueChange={setPlatform}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Platform" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All platforms</SelectItem>
              <SelectItem value="gumroad">Gumroad</SelectItem>
              <SelectItem value="lemonsqueezy">LemonSqueezy</SelectItem>
              <SelectItem value="etsy">Etsy</SelectItem>
              <SelectItem value="shopify">Shopify</SelectItem>
              <SelectItem value="direct">Direct</SelectItem>
            </SelectContent>
          </Select>
          <Select value={status} onValueChange={setStatus}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-cortex-border bg-cortex-surface p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-8 w-8 rounded-lg" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-3.5 w-24" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <Skeleton className="h-14" />
                  <Skeleton className="h-14" />
                </div>
                <Skeleton className="h-4 w-full" />
              </div>
            ))}
          </div>
        ) : products.length === 0 ? (
          <EmptyState
            icon={Package}
            title="No products found"
            description="Add your first product to start tracking revenue"
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
