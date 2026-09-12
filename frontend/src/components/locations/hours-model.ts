import type { LocationHoursPeriod } from "@/services/api/locations";

export const WEEK_DAYS = [
  "MONDAY",
  "TUESDAY",
  "WEDNESDAY",
  "THURSDAY",
  "FRIDAY",
  "SATURDAY",
  "SUNDAY",
] as const;

/**
 * Google keeps several sets of hours on one profile. Only the regular week is
 * editable here; anything else is carried through an edit untouched.
 */
export const REGULAR_HOURS_TYPE = "REGULAR";

const DAY_LABELS: Record<string, string> = {
  MONDAY: "Monday",
  TUESDAY: "Tuesday",
  WEDNESDAY: "Wednesday",
  THURSDAY: "Thursday",
  FRIDAY: "Friday",
  SATURDAY: "Saturday",
  SUNDAY: "Sunday",
};

export function normalizeToken(value: string) {
  return value.trim().toUpperCase();
}

/** "SPECIAL_HOURS" becomes "Special hours". */
export function humanizeToken(value: string) {
  const words = normalizeToken(value).split(/[\s_]+/).filter(Boolean);
  if (words.length === 0) return value;
  const [first, ...rest] = words;
  return [
    first.charAt(0) + first.slice(1).toLowerCase(),
    ...rest.map((word) => word.toLowerCase()),
  ].join(" ");
}

export function dayLabel(day: string) {
  return DAY_LABELS[normalizeToken(day)] ?? humanizeToken(day);
}

function clampHour(hour: number) {
  return Math.min(Math.max(Math.trunc(hour) || 0, 0), 23);
}

function clampMinute(minute: number) {
  return Math.min(Math.max(Math.trunc(minute) || 0, 0), 59);
}

export function formatClock(hour: number, minute: number) {
  const safeHour = ((Math.trunc(hour) % 24) + 24) % 24;
  const safeMinute = clampMinute(minute);
  const suffix = safeHour < 12 ? "AM" : "PM";
  const displayHour = safeHour % 12 === 0 ? 12 : safeHour % 12;
  return `${displayHour}:${String(safeMinute).padStart(2, "0")} ${suffix}`;
}

/**
 * A period is described relative to the day it opens on, because Google allows
 * several periods on one day and periods that close on a later day.
 */
export function describePeriod(period: LocationHoursPeriod) {
  const openDay = normalizeToken(period.open_day);
  const closeDay = normalizeToken(period.close_day);
  const spansDays = Boolean(closeDay) && closeDay !== openDay;
  const isFullDay =
    period.open_hour === 0 &&
    period.open_minute === 0 &&
    period.close_hour === 0 &&
    period.close_minute === 0;

  if (isFullDay && spansDays) return "Open 24 hours";

  const range = `${formatClock(period.open_hour, period.open_minute)} – ${formatClock(period.close_hour, period.close_minute)}`;
  return spansDays ? `${range} (${dayLabel(closeDay)})` : range;
}

/** A single row of the hours editor. `key` is local state only and never sent. */
export interface HoursDraftPeriod {
  key: string;
  openDay: string;
  /** "HH:MM" in 24-hour form, matching the value of an `input[type=time]`. */
  openTime: string;
  closeDay: string;
  closeTime: string;
}

let sequence = 0;

function nextKey() {
  sequence += 1;
  return `hours-period-${sequence}`;
}

export function toTimeValue(hour: number, minute: number) {
  return `${String(clampHour(hour)).padStart(2, "0")}:${String(clampMinute(minute)).padStart(2, "0")}`;
}

export function parseTimeValue(value: string) {
  const match = /^(\d{1,2}):(\d{2})/.exec(value.trim());
  if (!match) return null;
  const hour = Number(match[1]);
  const minute = Number(match[2]);
  if (!Number.isInteger(hour) || hour < 0 || hour > 23) return null;
  if (!Number.isInteger(minute) || minute < 0 || minute > 59) return null;
  return { hour, minute };
}

function isRegular(period: LocationHoursPeriod) {
  return (normalizeToken(period.hours_type) || REGULAR_HOURS_TYPE) === REGULAR_HOURS_TYPE;
}

export function regularPeriods(hours: LocationHoursPeriod[]) {
  return hours.filter(isRegular);
}

/** Holiday, special and other hour sets, which the editor preserves as they are. */
export function nonRegularPeriods(hours: LocationHoursPeriod[]) {
  return hours.filter((period) => !isRegular(period));
}

export function toDraftPeriods(hours: LocationHoursPeriod[]): HoursDraftPeriod[] {
  return regularPeriods(hours).map((period) => {
    const openDay = normalizeToken(period.open_day);
    return {
      key: nextKey(),
      openDay,
      openTime: toTimeValue(period.open_hour, period.open_minute),
      closeDay: normalizeToken(period.close_day) || openDay,
      closeTime: toTimeValue(period.close_hour, period.close_minute),
    };
  });
}

export function createDraftPeriod(openDay: string): HoursDraftPeriod {
  return {
    key: nextKey(),
    openDay,
    openTime: "09:00",
    closeDay: openDay,
    closeTime: "17:00",
  };
}

/** The days the editor shows: the full week, plus anything unexpected in the data. */
export function editableDays(periods: HoursDraftPeriod[]): string[] {
  const extra = periods
    .map((period) => period.openDay)
    .filter((day) => day && !WEEK_DAYS.includes(day as (typeof WEEK_DAYS)[number]));
  return [...WEEK_DAYS, ...[...new Set(extra)]];
}

export function draftPeriodError(period: HoursDraftPeriod): string | null {
  const open = parseTimeValue(period.openTime);
  const close = parseTimeValue(period.closeTime);
  if (!open || !close) return "Enter both an opening and a closing time.";
  if (!period.closeDay) return "Choose the day this period closes on.";
  if (period.closeDay !== period.openDay) return null;

  const openMinutes = open.hour * 60 + open.minute;
  const closeMinutes = close.hour * 60 + close.minute;
  if (closeMinutes <= openMinutes) {
    return "The closing time must be later than the opening time, or close on a later day.";
  }
  return null;
}

/** Keyed by the draft period key, so an error can be shown on the row that caused it. */
export function draftPeriodErrors(periods: HoursDraftPeriod[]): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const period of periods) {
    const error = draftPeriodError(period);
    if (error) errors[period.key] = error;
  }
  return errors;
}

function dayOrder(day: string) {
  const index = WEEK_DAYS.indexOf(day as (typeof WEEK_DAYS)[number]);
  return index === -1 ? WEEK_DAYS.length : index;
}

/**
 * Builds the payload for the API: the edited regular week in week order, followed by
 * the hour sets the editor does not touch.
 */
export function toApiPeriods(
  periods: HoursDraftPeriod[],
  preserved: LocationHoursPeriod[] = [],
): LocationHoursPeriod[] {
  const edited = [...periods]
    .sort((a, b) => dayOrder(a.openDay) - dayOrder(b.openDay) || a.openTime.localeCompare(b.openTime))
    .flatMap((period) => {
      const open = parseTimeValue(period.openTime);
      const close = parseTimeValue(period.closeTime);
      if (!open || !close) return [];
      return [
        {
          hours_type: REGULAR_HOURS_TYPE,
          open_day: period.openDay,
          open_hour: open.hour,
          open_minute: open.minute,
          close_day: period.closeDay || period.openDay,
          close_hour: close.hour,
          close_minute: close.minute,
        },
      ];
    });

  return [...edited, ...preserved];
}
