import { cn } from "@/utils/cn";
import type { ReactNode } from "react";

interface PageHeaderProps {
  title: ReactNode;
  description?: ReactNode;
  /** Rendered above the title — a back link or breadcrumb. */
  above?: ReactNode;
  /** Rendered below the description — status chips or counts. */
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

export function PageHeader({
  title,
  description,
  above,
  meta,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between",
        className,
      )}
    >
      <div className="min-w-0 max-w-2xl">
        {above}
        <h1 className="text-[26px] leading-8 font-semibold tracking-[-0.03em] break-words text-text-primary sm:text-[28px] sm:leading-9">
          {title}
        </h1>
        {description ? (
          <p className="mt-2 text-sm leading-6 text-text-tertiary">{description}</p>
        ) : null}
        {meta ? <div className="mt-4 flex flex-wrap items-center gap-2">{meta}</div> : null}
      </div>
      {actions ? (
        <div className="flex shrink-0 flex-wrap items-center gap-2.5">{actions}</div>
      ) : null}
    </header>
  );
}
