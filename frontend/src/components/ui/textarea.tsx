import * as React from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[80px] w-full rounded-md border border-cortex-border bg-cortex-surface px-3 py-2 text-sm text-cortex-text shadow-sm",
          "placeholder:text-cortex-muted",
          "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-cortex-accent focus-visible:border-cortex-accent/70",
          "disabled:cursor-not-allowed disabled:opacity-50",
          "resize-none",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";

export { Textarea };
