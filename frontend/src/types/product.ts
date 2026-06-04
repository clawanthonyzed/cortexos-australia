export type ProductStatus = "draft" | "active" | "paused" | "archived";
export type ProductPlatform = "gumroad" | "lemonsqueezy" | "etsy" | "shopify" | "direct";
export type ProductType = "digital_download" | "subscription" | "physical" | "service" | "template";

export interface ProductSalesData {
  date: string;
  revenue: number;
  units: number;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  type: ProductType;
  status: ProductStatus;
  platform: ProductPlatform;
  platformId: string | null;
  platformUrl: string | null;
  venture: string | null;
  priceAud: number;
  currency: string;
  totalRevenue: number;
  totalUnits: number;
  revenueThisMonth: number;
  unitsThisMonth: number;
  conversionRate: number | null;
  rating: number | null;
  reviewCount: number;
  tags: string[];
  imageUrl: string | null;
  salesHistory: ProductSalesData[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateProductInput {
  name: string;
  description: string;
  type: ProductType;
  platform: ProductPlatform;
  venture: string | null;
  priceAud: number;
  tags: string[];
  imageUrl: string | null;
}
