"use client";

import { cn } from "@/utils/cn";

export interface ChartLegendItem {
  key: string;
  label: string;
  color: string;
  /** Hidden by the reader. The colour never moves to another series because of it. */
  isHidden?: boolean;
  /** Google returned no value for this metric anywhere in the range. */
  isUnavailable?: boolean;
}

interface ChartLegendProps {
  items: ChartLegendItem[];
  label: string;
  /** Omit to render a plain, non-interactive key. */
  onToggle?: (key: string) => void;
  className?: string;
}

function LineKey({ color, isMuted }: { color: string; isMuted: boolean }) {
  return (
    <span
      aria-hidden="true"
      className={cn("h-0.5 w-4 shrink-0 rounded-full", isMuted && "opacity-30")}
      style={{ backgroundColor: color }}
    />
  );
}

export function ChartLegend({ items, label, onToggle, className }: ChartLegendProps) {
  if (!onToggle) {
    return (
      <ul
        aria-label={label}
        className={cn("flex flex-wrap items-center gap-x-4 gap-y-2", className)}
      >
        {items.map((item) => (
          <li key={item.key} className="flex items-center gap-2 text-xs text-text-secondary">
            <LineKey color={item.color} isMuted={Boolean(item.isUnavailable)} />
            <span>{item.label}</span>
            {item.isUnavailable ? (
              <span className="text-text-tertiary">· not reported</span>
            ) : null}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div role="group" aria-label={label} className={cn("flex flex-wrap gap-1", className)}>
      {items.map((item) => {
        const isOff = Boolean(item.isHidden) || Boolean(item.isUnavailable);
        return (
          <button
            key={item.key}
            type="button"
            aria-pressed={!isOff}
            disabled={item.isUnavailable}
            onClick={() => onToggle(item.key)}
            className={cn(
              "flex h-11 items-center gap-2 rounded-lg px-2.5 text-xs font-medium transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
              item.isUnavailable
                ? "cursor-not-allowed text-text-disable"
                : "hover:bg-background-gray-secondary",
              isOff ? "text-text-tertiary" : "text-text-primary",
            )}
          >
            <LineKey color={item.color} isMuted={isOff} />
            <span>{item.label}</span>
            {item.isUnavailable ? <span className="font-normal">· not reported</span> : null}
          </button>
        );
      })}
    </div>
  );
}
