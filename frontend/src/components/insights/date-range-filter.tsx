"use client";

import { cn } from "@/utils/cn";
import { format, subDays } from "date-fns";
import { useId } from "react";
import { formatPointDate } from "./chart-series";

export type DateRangePresetId = "7d" | "30d" | "90d" | "custom";

export interface DateRangeValue {
  preset: DateRangePresetId;
  /** `YYYY-MM-DD`, inclusive. */
  from: string;
  /** `YYYY-MM-DD`, inclusive. */
  to: string;
}

const PRESETS: {
  id: Exclude<DateRangePresetId, "custom">;
  label: string;
  days: number;
}[] = [
  { id: "7d", label: "Last 7 days", days: 7 },
  { id: "30d", label: "Last 30 days", days: 30 },
  { id: "90d", label: "Last 90 days", days: 90 },
];

function isoDate(date: Date) {
  return format(date, "yyyy-MM-dd");
}

export function todayIso() {
  return isoDate(new Date());
}

export function presetRange(id: Exclude<DateRangePresetId, "custom">): DateRangeValue {
  const days = PRESETS.find((preset) => preset.id === id)?.days ?? 30;
  const today = new Date();
  return {
    preset: id,
    from: isoDate(subDays(today, days - 1)),
    to: isoDate(today),
  };
}

/** The range a reader most often wants first, and the one the page opens on. */
export function defaultDateRange() {
  return presetRange("30d");
}

interface DateRangeFilterProps {
  value: DateRangeValue;
  onChange: (value: DateRangeValue) => void;
}

const inputClassName =
  "h-11 w-full rounded-lg border border-border-primary bg-card-background px-3 text-sm text-text-primary outline-none focus-visible:border-primary-500 focus-visible:ring-2 focus-visible:ring-primary-500 sm:w-auto";

export function DateRangeFilter({ value, onChange }: DateRangeFilterProps) {
  const fromId = useId();
  const toId = useId();
  const maxDate = todayIso();

  function selectCustom() {
    onChange({ ...value, preset: "custom" });
  }

  function changeFrom(from: string) {
    if (!from) return;
    onChange({ preset: "custom", from, to: from > value.to ? from : value.to });
  }

  function changeTo(to: string) {
    if (!to) return;
    onChange({ preset: "custom", from: to < value.from ? to : value.from, to });
  }

  return (
    <div className="flex flex-col gap-3">
      <div
        role="group"
        aria-label="Reporting period"
        className="flex w-full flex-wrap gap-1 rounded-lg bg-background-gray-secondary p-1 sm:w-auto sm:self-start"
      >
        {PRESETS.map((preset) => {
          const isActive = value.preset === preset.id;
          return (
            <button
              key={preset.id}
              type="button"
              aria-pressed={isActive}
              onClick={() => onChange(presetRange(preset.id))}
              className={cn(
                "flex h-11 flex-1 items-center justify-center rounded-md px-3 text-sm font-medium whitespace-nowrap transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500 sm:flex-none sm:px-4",
                isActive
                  ? "bg-background-gray-secondary_alt_2 text-white-100"
                  : "text-text-secondary hover:text-text-primary",
              )}
            >
              {preset.label}
            </button>
          );
        })}
        <button
          type="button"
          aria-pressed={value.preset === "custom"}
          onClick={selectCustom}
          className={cn(
            "flex h-11 flex-1 items-center justify-center rounded-md px-3 text-sm font-medium whitespace-nowrap transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500 sm:flex-none sm:px-4",
            value.preset === "custom"
              ? "bg-background-gray-secondary_alt_2 text-white-100"
              : "text-text-secondary hover:text-text-primary",
          )}
        >
          Custom
        </button>
      </div>

      {value.preset === "custom" ? (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex flex-col gap-1.5">
            <label htmlFor={fromId} className="text-xs font-medium text-text-secondary">
              From
            </label>
            <input
              id={fromId}
              type="date"
              value={value.from}
              max={maxDate}
              onChange={(event) => changeFrom(event.target.value)}
              className={inputClassName}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={toId} className="text-xs font-medium text-text-secondary">
              To
            </label>
            <input
              id={toId}
              type="date"
              value={value.to}
              max={maxDate}
              onChange={(event) => changeTo(event.target.value)}
              className={inputClassName}
            />
          </div>
        </div>
      ) : null}

      <p aria-live="polite" className="text-xs leading-5 text-text-tertiary">
        Showing {formatPointDate(value.from)} to {formatPointDate(value.to)}.
      </p>
    </div>
  );
}
