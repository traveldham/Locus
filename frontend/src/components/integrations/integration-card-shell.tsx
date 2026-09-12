import { cn } from "@/utils/cn";
import { Google } from "@tailgrids/icons";
import type { ReactNode } from "react";

export interface IntegrationCardShellProps {
  title: string;
  description: string;
  /** Status chip rendered beside the title. */
  status?: ReactNode;
  children: ReactNode;
  className?: string;
}

/** Shared chrome for the Google Business Profile card in both connection states. */
export function IntegrationCardShell({
  title,
  description,
  status,
  children,
  className,
}: IntegrationCardShellProps) {
  return (
    <section
      aria-labelledby="google-integration-title"
      className={cn("rounded-xl border border-card-border bg-card-background", className)}
    >
      <div className="flex flex-col gap-4 border-b border-card-border p-5 sm:flex-row sm:items-start sm:gap-5 sm:p-6">
        <span
          aria-hidden="true"
          className="flex size-11 shrink-0 items-center justify-center rounded-xl border border-card-border bg-background-gray-secondary text-icon-primary [&>svg]:size-6"
        >
          <Google />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
            <h2 id="google-integration-title" className="text-base font-semibold text-text-primary">
              {title}
            </h2>
            {status}
          </div>
          <p className="mt-1.5 max-w-prose text-sm leading-6 text-text-tertiary">{description}</p>
        </div>
      </div>
      <div className="p-5 sm:p-6">{children}</div>
    </section>
  );
}
