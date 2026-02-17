import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  className?: string;
  /** Render a full-page centered spinner (default: true) */
  fullPage?: boolean;
}

export function LoadingSpinner({ className, fullPage = true }: LoadingSpinnerProps) {
  const spinner = (
    <Loader2 className={cn("h-6 w-6 animate-spin text-muted-foreground", className)} />
  );

  if (fullPage) {
    return (
      <div className="flex items-center justify-center py-20">
        {spinner}
      </div>
    );
  }

  return spinner;
}

