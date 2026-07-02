import * as React from "react";

import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        ref={ref}
        className={cn(
          "min-h-24 w-full resize-y rounded-md border border-white/10 bg-white/[0.04] px-3 py-3 text-sm text-board-mist outline-none transition placeholder:text-board-muted focus:border-board-teal/70 focus:bg-white/[0.07] focus:ring-2 focus:ring-board-teal/15",
          className
        )}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";

export { Textarea };
