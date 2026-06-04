import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  label?: string;
}

const sizeClasses = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-10 w-10",
};

export function LoadingSpinner({ size = "md", className, label }: LoadingSpinnerProps) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Loader2 className={cn("animate-spin text-cortex-accent", sizeClasses[size])} />
      {label && <span className="text-sm text-cortex-muted">{label}</span>}
    </div>
  );
}

export function PageLoader({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex h-full min-h-[400px] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="h-8 w-8 animate-spin text-cortex-accent" />
        <p className="text-sm text-cortex-muted">{label}</p>
      </div>
    </div>
  );
}
