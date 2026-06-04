import { cn } from "@/lib/utils";

interface StatusDotProps {
  status: "idle" | "running" | "paused" | "error" | "stopped" | "active" | "draft" | "archived";
  size?: "sm" | "md" | "lg";
  pulse?: boolean;
  className?: string;
}

const sizeClasses = {
  sm: "h-1.5 w-1.5",
  md: "h-2.5 w-2.5",
  lg: "h-3 w-3",
};

const colorClasses = {
  running: "bg-cortex-success",
  active: "bg-cortex-success",
  idle: "bg-cortex-muted",
  stopped: "bg-cortex-muted",
  archived: "bg-cortex-muted",
  paused: "bg-cortex-warning",
  draft: "bg-cortex-warning",
  error: "bg-cortex-error",
};

export function StatusDot({ status, size = "md", pulse = false, className }: StatusDotProps) {
  const color = colorClasses[status] ?? "bg-cortex-muted";
  const shouldPulse = pulse && (status === "running" || status === "active");

  return (
    <span className={cn("relative inline-flex", sizeClasses[size], className)}>
      {shouldPulse && (
        <span
          className={cn(
            "absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping",
            color
          )}
        />
      )}
      <span className={cn("relative inline-flex rounded-full", sizeClasses[size], color)} />
    </span>
  );
}
