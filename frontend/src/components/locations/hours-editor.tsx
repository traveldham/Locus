"use client";

import { Button } from "@/components/tailgrids/core/button";
import { cn } from "@/utils/cn";
import { Plus, Trash1 } from "@tailgrids/icons";
import { useId, useRef } from "react";
import {
  WEEK_DAYS,
  createDraftPeriod,
  dayLabel,
  editableDays,
  type HoursDraftPeriod,
} from "./hours-model";

/**
 * Native time and select controls keep the keyboard, locale and screen-reader
 * behaviour the platform already provides. The browser paints its own clock and
 * arrow affordances from the `color-scheme` the theme provider sets on the document.
 */
const CONTROL_CLASS =
  "h-11 rounded-lg border border-card-border bg-input-background px-3 text-sm text-text-primary tabular-nums outline-none transition focus:border-input-primary-focus-border focus:ring-4 focus:ring-input-primary-focus-border/20 disabled:cursor-not-allowed disabled:text-text-disable aria-[invalid=true]:border-input-error-focus-border aria-[invalid=true]:focus:ring-input-error-focus-border/20";

function closeDayOptionLabel(day: string, openDay: string) {
  const label = dayLabel(day);
  if (day === openDay) return `${label} (same day)`;

  const openIndex = WEEK_DAYS.indexOf(openDay as (typeof WEEK_DAYS)[number]);
  const dayIndex = WEEK_DAYS.indexOf(day as (typeof WEEK_DAYS)[number]);
  if (openIndex !== -1 && dayIndex === (openIndex + 1) % WEEK_DAYS.length) {
    return `${label} (next day)`;
  }
  return label;
}

interface HoursEditorProps {
  periods: HoursDraftPeriod[];
  onChange: (periods: HoursDraftPeriod[]) => void;
  /** Keyed by draft period key, so a message sits on the row that caused it. */
  errors: Record<string, string>;
  /** A message the API returned against the `hours` field as a whole. */
  fieldError?: string | null;
  /** Holiday and other hour sets that this editor carries through unchanged. */
  preservedCount?: number;
  /**
   * True while the profile has no regular week at all. An empty day then means
   * "not set", which is not the same thing as the profile saying it is closed.
   */
  isUnset?: boolean;
  disabled?: boolean;
}

export function HoursEditor({
  periods,
  onChange,
  errors,
  fieldError,
  preservedCount = 0,
  isUnset = false,
  disabled = false,
}: HoursEditorProps) {
  const groupId = useId();
  const focusKeyRef = useRef<string | null>(null);
  const days = editableDays(periods);

  function updatePeriod(key: string, patch: Partial<HoursDraftPeriod>) {
    onChange(periods.map((period) => (period.key === key ? { ...period, ...patch } : period)));
  }

  function addPeriod(day: string) {
    const created = createDraftPeriod(day);
    focusKeyRef.current = created.key;
    onChange([...periods, created]);
  }

  function removePeriod(key: string) {
    onChange(periods.filter((period) => period.key !== key));
  }

  function registerOpenTime(key: string) {
    return (node: HTMLInputElement | null) => {
      if (node && focusKeyRef.current === key) {
        focusKeyRef.current = null;
        node.focus();
      }
    };
  }

  return (
    <div>
      {fieldError ? (
        <p
          role="alert"
          className="mb-4 rounded-lg bg-alert-danger-background px-3 py-2.5 text-sm leading-5 text-alert-danger-description"
        >
          {fieldError}
        </p>
      ) : null}

      {isUnset ? (
        <p className="rounded-lg border border-dashed border-card-border px-4 py-3 text-sm leading-6 text-text-tertiary">
          This profile has no regular opening hours on Google yet. Adding hours to any
          day publishes the whole week, and every day left empty is published as closed.
        </p>
      ) : (
        <p className="text-sm leading-6 text-text-tertiary">
          A day with no hours is published as closed. Add a second period for a midday
          break, and set a later closing day for hours that run past midnight.
        </p>
      )}

      <ul className="mt-2 divide-y divide-card-border">
        {days.map((day) => {
          const dayPeriods = periods.filter((period) => period.openDay === day);
          const headingId = `${groupId}-${day}`;

          return (
            <li key={day} className="py-4 first:pt-3 last:pb-0">
              <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
                <div className="flex min-w-0 items-center gap-2.5">
                  <h3 id={headingId} className="text-sm font-medium text-text-primary">
                    {dayLabel(day)}
                  </h3>
                  {dayPeriods.length === 0 ? (
                    <span className="inline-flex items-center rounded-full bg-badge-neutral-background px-2 py-0.5 text-xs font-medium text-badge-neutral-text">
                      {isUnset ? "Not set" : "Closed"}
                    </span>
                  ) : null}
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-11 shrink-0 px-3"
                  isDisabled={disabled}
                  onPress={() => addPeriod(day)}
                  aria-describedby={headingId}
                >
                  <Plus aria-hidden="true" focusable="false" />
                  Add hours
                </Button>
              </div>

              {dayPeriods.length > 0 ? (
                <ul className="mt-2.5 space-y-2.5" aria-labelledby={headingId}>
                  {dayPeriods.map((period, index) => {
                    const error = errors[period.key];
                    const errorId = `${period.key}-error`;
                    const position = `${dayLabel(day)} period ${index + 1}`;

                    return (
                      <li key={period.key}>
                        <div className="flex flex-wrap items-center gap-x-2 gap-y-2">
                          <input
                            ref={registerOpenTime(period.key)}
                            type="time"
                            value={period.openTime}
                            disabled={disabled}
                            aria-label={`${position} opening time`}
                            aria-invalid={error ? true : undefined}
                            aria-describedby={error ? errorId : undefined}
                            onChange={(event) =>
                              updatePeriod(period.key, { openTime: event.target.value })
                            }
                            className={cn(CONTROL_CLASS, "w-30")}
                          />
                          <span aria-hidden="true" className="text-sm text-text-tertiary">
                            –
                          </span>
                          <input
                            type="time"
                            value={period.closeTime}
                            disabled={disabled}
                            aria-label={`${position} closing time`}
                            aria-invalid={error ? true : undefined}
                            aria-describedby={error ? errorId : undefined}
                            onChange={(event) =>
                              updatePeriod(period.key, { closeTime: event.target.value })
                            }
                            className={cn(CONTROL_CLASS, "w-30")}
                          />
                          <select
                            value={period.closeDay}
                            disabled={disabled}
                            aria-label={`${position} closing day`}
                            onChange={(event) =>
                              updatePeriod(period.key, { closeDay: event.target.value })
                            }
                            className={cn(CONTROL_CLASS, "min-w-0 flex-1 pr-8 sm:flex-none")}
                          >
                            {[
                              ...WEEK_DAYS,
                              ...(WEEK_DAYS.includes(
                                period.closeDay as (typeof WEEK_DAYS)[number],
                              )
                                ? []
                                : [period.closeDay]),
                            ].map((option) => (
                              <option key={option} value={option}>
                                {closeDayOptionLabel(option, period.openDay)}
                              </option>
                            ))}
                          </select>
                          <Button
                            type="button"
                            variant="danger"
                            appearance="ghost"
                            size="xl"
                            iconOnly
                            className="shrink-0"
                            isDisabled={disabled}
                            onPress={() => removePeriod(period.key)}
                            aria-label={`Remove ${position}`}
                          >
                            <Trash1 aria-hidden="true" focusable="false" />
                          </Button>
                        </div>
                        {error ? (
                          <p id={errorId} className="mt-1.5 text-xs leading-5 text-input-error">
                            {error}
                          </p>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              ) : null}
            </li>
          );
        })}
      </ul>

      {preservedCount > 0 ? (
        <p className="mt-4 border-t border-card-border pt-4 text-xs leading-5 text-text-tertiary">
          {preservedCount === 1
            ? "1 period from another set of hours on this profile, such as holiday hours, is sent back to Google unchanged."
            : `${preservedCount} periods from other sets of hours on this profile, such as holiday hours, are sent back to Google unchanged.`}
        </p>
      ) : null}
    </div>
  );
}
