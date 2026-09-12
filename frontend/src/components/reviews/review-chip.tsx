import { cn } from "@/utils/cn";
import type { ReactNode } from "react";

/**
 * Only the tokens that are defined in both themes are used here, and the label
 * always carries the meaning so nothing depends on colour alone.
 */
const TONE_STYLES = {
  attention: "bg-badge-warning-background text-badge-warning-text",
  neutral: "bg-badge-neutral-background text-badge-neutral-text",
} as const;

const TONE_MARKERS = {
  attention: "bg-badge-warning-icon-color",
  neutral: "bg-badge-neutral-icon-color",
} as const;

export interface ReviewChipProps {
  tone?: keyof typeof TONE_STYLES;
  children: ReactNode;
  className?: string;
}

export function ReviewChip({ tone = "neutral", children, className }: ReviewChipProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs leading-4 font-medium whitespace-nowrap",
        TONE_STYLES[tone],
        className,
      )}
    >
      <span aria-hidden="true" className={cn("size-1.5 shrink-0 rounded-full", TONE_MARKERS[tone])} />
      {children}
    </span>
  );
}
