import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow, parseISO, isValid } from "date-fns";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatCurrency(
  amount: number,
  currency: string = "AUD",
  compact: boolean = false
): string {
  if (compact && Math.abs(amount) >= 1000) {
    const divided = amount / 1000;
    return new Intl.NumberFormat("en-AU", {
      style: "currency",
      currency,
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(divided) + "K";
  }
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) {
    return `${(tokens / 1_000_000).toFixed(2)}M`;
  }
  if (tokens >= 1_000) {
    return `${(tokens / 1_000).toFixed(1)}K`;
  }
  return tokens.toString();
}

export function formatBytes(bytes: number): string {
  if (bytes >= 1_073_741_824) {
    return `${(bytes / 1_073_741_824).toFixed(2)} GB`;
  }
  if (bytes >= 1_048_576) {
    return `${(bytes / 1_048_576).toFixed(2)} MB`;
  }
  if (bytes >= 1_024) {
    return `${(bytes / 1_024).toFixed(1)} KB`;
  }
  return `${bytes} B`;
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60_000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3_600_000) {
    const min = Math.floor(ms / 60_000);
    const sec = Math.floor((ms % 60_000) / 1000);
    return `${min}m ${sec}s`;
  }
  const hr = Math.floor(ms / 3_600_000);
  const min = Math.floor((ms % 3_600_000) / 60_000);
  return `${hr}h ${min}m`;
}

export function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return "Never";
  const date = parseISO(dateString);
  if (!isValid(date)) return "Invalid date";
  return formatDistanceToNow(date, { addSuffix: true });
}

export function formatDate(
  dateString: string | null,
  fmt: string = "MMM d, yyyy"
): string {
  if (!dateString) return "-";
  const date = parseISO(dateString);
  if (!isValid(date)) return "Invalid date";
  return format(date, fmt);
}

export function formatDateTime(dateString: string | null): string {
  return formatDate(dateString, "MMM d, yyyy HH:mm");
}

export function formatPercent(value: number, decimals: number = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength - 3)}...`;
}

export function slugify(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function getDelta(current: number, previous: number): number {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
}

export function colorFromStatus(
  status: string
): "success" | "warning" | "error" | "muted" | "accent" {
  switch (status) {
    case "running":
    case "active":
    case "completed":
      return "success";
    case "paused":
    case "queued":
      return "warning";
    case "error":
    case "failed":
      return "error";
    case "idle":
    case "stopped":
    case "archived":
      return "muted";
    default:
      return "accent";
  }
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 11);
}
