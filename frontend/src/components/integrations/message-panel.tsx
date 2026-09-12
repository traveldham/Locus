import { cn } from "@/utils/cn";
import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";

const iconTileStyles = cva("flex size-10 shrink-0 items-center justify-center rounded-xl [&>svg]:size-5", {
  variants: {
    tone: {
      neutral: "bg-background-gray-tertiary text-icon-secondary",
      error: "bg-badge-error-background text-badge-error-text",
    },
  },
  defaultVariants: { tone: "neutral" },
});

export interface MessagePanelProps extends VariantProps<typeof iconTileStyles> {
  icon: ReactNode;
  title: string;
  description: ReactNode;
  /** Action buttons or links rendered under the description. */
  children?: ReactNode;
  className?: string;
}

/** Centred panel used for the terminal states of a request: nothing found, or failed. */
export function MessagePanel({ icon, title, description, tone, children, className }: MessagePanelProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center rounded-xl border border-card-border bg-card-background px-6 py-12 text-center",
        className,
      )}
    >
      <span aria-hidden="true" className={iconTileStyles({ tone })}>
        {icon}
      </span>
      <h2 className="mt-4 text-base font-semibold text-text-primary">{title}</h2>
      <div className="mt-2 max-w-prose text-sm leading-6 text-text-tertiary">{description}</div>
      {children && <div className="mt-6 flex flex-wrap items-center justify-center gap-3">{children}</div>}
    </div>
  );
}
