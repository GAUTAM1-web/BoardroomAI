import * as React from "react";

import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={cn(
        "h-10 w-full rounded-md border border-white/10 bg-white/[0.04] px-3 text-sm text-board-mist outline-none transition placeholder:text-board-muted focus:border-board-teal/70 focus:bg-white/[0.07] focus:ring-2 focus:ring-board-teal/15",
        className
      )}
      {...props}
    />
  );
});
Input.displayName = "Input";

export { Input };
