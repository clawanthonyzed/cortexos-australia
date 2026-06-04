import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-cortex-accent/20 text-indigo-300",
        success:
          "border-transparent bg-cortex-success/15 text-green-400",
        warning:
          "border-transparent bg-cortex-warning/15 text-amber-400",
        error:
          "border-transparent bg-cortex-error/15 text-red-400",
        muted:
          "border-cortex-border bg-cortex-surface text-cortex-muted",
        outline:
          "border-cortex-border text-cortex-muted bg-transparent",
        accent:
          "border-cortex-accent/30 bg-cortex-accent/10 text-indigo-300",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
