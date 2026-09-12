import { cn } from "@/utils/cn";
import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

/**
 * Tone never carries meaning on its own: every chip also renders its label as
 * text, so the state is readable without relying on colour perception.
 */
const statusChipStyles = cva(
  "inline-flex max-w-full items-center gap-1.5 rounded-md border border-current/20 px-2 py-1 text-xs leading-4 font-medium whitespace-nowrap",
  {
    variants: {
      tone: {
        neutral: "bg-badge-neutral-background text-badge-neutral-text",
        positive: "bg-badge-success-background text-badge-success-text",
        caution: "bg-badge-warning-background text-badge-warning-text",
        critical: "bg-badge-error-background text-badge-error-text",
        info: "bg-badge-primary-background text-badge-primary-text",
      },
    },
    defaultVariants: {
      tone: "neutral",
    },
  },
);

export type StatusChipTone = NonNullable<VariantProps<typeof statusChipStyles>["tone"]>;

function StatusChipDot() {
  return <span aria-hidden="true" className="size-1.5 shrink-0 rounded-full bg-current" />;
}

export interface StatusChipProps extends Omit<ComponentProps<"span">, "children"> {
  tone?: StatusChipTone;
  label: string;
  /** Hide the leading dot when the chip already carries an icon or sits alone. */
  showDot?: boolean;
}

export function StatusChip({ tone, label, showDot = true, className, ...props }: StatusChipProps) {
  return (
    <span className={cn(statusChipStyles({ tone }), className)} {...props}>
      {showDot && <StatusChipDot />}
      <span className="truncate">{label}</span>
    </span>
  );
}
