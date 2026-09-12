import { cn } from "@/utils/cn";
import type { ReactNode } from "react";

/** An empty profile field is meaningful information, so it is labelled rather than left blank. */
export function NotSet() {
  return <span className="text-text-disable">Not set</span>;
}

interface DataFieldProps {
  label: string;
  children?: ReactNode;
  className?: string;
}

export function DataField({ label, children, className }: DataFieldProps) {
  const isEmpty =
    children === null || children === undefined || children === false || children === "";

  return (
    <div className={cn("min-w-0", className)}>
      <dt className="text-[11px] font-medium tracking-[0.08em] text-text-tertiary uppercase">
        {label}
      </dt>
      <dd className="mt-1.5 text-sm leading-6 break-words text-text-primary">
        {isEmpty ? <NotSet /> : children}
      </dd>
    </div>
  );
}
