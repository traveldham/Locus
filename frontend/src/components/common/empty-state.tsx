import { cn } from "@/utils/cn";
import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, actions, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center rounded-2xl border border-dashed border-card-border bg-card-background px-6 py-12 text-center sm:py-16",
        className,
      )}
    >
      {icon ? (
        <span className="mb-5 flex size-12 items-center justify-center rounded-xl bg-background-gray-secondary_alt_2 text-white-100 [&>svg]:size-5">
          {icon}
        </span>
      ) : null}
      <h2 className="text-lg font-semibold tracking-[-0.015em] text-text-primary">{title}</h2>
      <div className="mt-2 max-w-md text-sm leading-6 text-text-tertiary">{description}</div>
      {actions ? (
        <div className="mt-7 flex flex-col items-stretch gap-2.5 sm:flex-row sm:items-center sm:justify-center">
          {actions}
        </div>
      ) : null}
    </div>
  );
}
