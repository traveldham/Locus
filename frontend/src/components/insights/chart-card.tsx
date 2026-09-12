"use client";

import { SectionCard } from "@/components/common/section-card";
import { cn } from "@/utils/cn";
import { BarChart2, Table2 } from "@tailgrids/icons";
import { useId, useState, type ReactNode } from "react";
import styles from "./chart-theme.module.css";

type ChartView = "chart" | "table";

const VIEWS: { id: ChartView; label: string; icon: ReactNode }[] = [
  {
    id: "chart",
    label: "Chart",
    icon: <BarChart2 aria-hidden="true" focusable="false" />,
  },
  {
    id: "table",
    label: "Table",
    icon: <Table2 aria-hidden="true" focusable="false" />,
  },
];

interface ChartCardProps {
  title: string;
  icon?: ReactNode;
  /** What the chart plots, in one sentence. */
  description?: ReactNode;
  /** Read below the chart: what a gap means, and where the figures came from. */
  note?: ReactNode;
  chart: ReactNode;
  /**
   * The same numbers as a table. It is not a fallback: it is how a value is read
   * exactly, and how the chart stays usable without relying on colour.
   */
  table: ReactNode;
  /** True while a new slice is loading, so the frame is held rather than replaced. */
  isRefetching?: boolean;
  className?: string;
}

export function ChartCard({
  title,
  icon,
  description,
  note,
  chart,
  table,
  isRefetching = false,
  className,
}: ChartCardProps) {
  const [view, setView] = useState<ChartView>("chart");
  const groupId = useId();

  return (
    <SectionCard
      title={title}
      icon={icon}
      className={className}
      actions={
        <div
          role="group"
          aria-labelledby={groupId}
          className="flex gap-1 rounded-lg bg-background-gray-secondary p-1"
        >
          <span id={groupId} className="sr-only">
            {title} view
          </span>
          {VIEWS.map((option) => {
            const isActive = view === option.id;
            return (
              <button
                key={option.id}
                type="button"
                aria-pressed={isActive}
                onClick={() => setView(option.id)}
                className={cn(
                  "flex h-11 min-w-11 items-center justify-center gap-2 rounded-md px-3 text-sm font-medium transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500 [&>svg]:size-4",
                  isActive
                    ? "bg-background-gray-secondary_alt_2 text-white-100"
                    : "text-text-secondary hover:text-text-primary",
                )}
              >
                {option.icon}
                {option.label}
              </button>
            );
          })}
        </div>
      }
    >
      {description ? (
        <p className="mb-4 text-sm leading-6 text-text-tertiary">{description}</p>
      ) : null}

      <div
        aria-busy={isRefetching}
        className={cn(styles.scope, "transition-opacity", isRefetching && "opacity-60")}
      >
        {view === "chart" ? chart : table}
      </div>

      {note ? (
        <p className="mt-4 border-t border-card-border pt-4 text-xs leading-5 text-text-tertiary">
          {note}
        </p>
      ) : null}
    </SectionCard>
  );
}
