"use client";

import { cn } from "@/utils/cn";
import { useId, type ReactNode } from "react";

interface SectionCardProps {
  title: string;
  icon?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}

export function SectionCard({
  title,
  icon,
  actions,
  children,
  className,
  bodyClassName,
}: SectionCardProps) {
  const headingId = useId();

  return (
    <section
      aria-labelledby={headingId}
      className={cn("rounded-xl border border-card-border bg-card-background", className)}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-card-border px-5 py-3.5">
        <div className="flex min-w-0 items-center gap-2.5">
          {icon ? (
            <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-background-gray-secondary text-icon-secondary [&>svg]:size-4">
              {icon}
            </span>
          ) : null}
          <h2
            id={headingId}
            className="truncate text-sm font-semibold tracking-[-0.01em] text-text-primary"
          >
            {title}
          </h2>
        </div>
        {actions}
      </div>
      <div className={cn("px-5 py-5", bodyClassName)}>{children}</div>
    </section>
  );
}
