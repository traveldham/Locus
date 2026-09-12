import type {
  ActionMetricKey,
  ImpressionMetricKey,
  PerformancePoint,
} from "@/services/api/insights";
import { format, isValid, parseISO } from "date-fns";

export interface SeriesSpec<K extends string> {
  key: K;
  label: string;
  /** A CSS variable from `chart-theme.module.css`, so it swaps with the theme. */
  color: string;
}

/**
 * Colour follows the metric, never its position in the current view. Hiding a
 * series from the chart therefore never repaints the ones that remain.
 */
export const ACTION_SERIES: SeriesSpec<ActionMetricKey>[] = [
  {
    key: "website_clicks",
    label: "Website clicks",
    color: "var(--viz-series-1)",
  },
  { key: "call_clicks", label: "Calls", color: "var(--viz-series-2)" },
  {
    key: "direction_requests",
    label: "Direction requests",
    color: "var(--viz-series-3)",
  },
  {
    key: "conversations",
    label: "Conversations",
    color: "var(--viz-series-4)",
  },
  { key: "bookings", label: "Bookings", color: "var(--viz-series-5)" },
];

/**
 * The four impression fields as table columns and headline figures. Device drives
 * the colour, so the two desktop entries share a hue and the two mobile entries
 * share another — never plot all four on one set of axes with these specs; use
 * `IMPRESSION_FACETS`, which separates them by surface.
 */
export const IMPRESSION_SERIES: SeriesSpec<ImpressionMetricKey>[] = [
  {
    key: "impressions_maps_desktop",
    label: "Maps · Desktop",
    color: "var(--viz-series-1)",
  },
  {
    key: "impressions_maps_mobile",
    label: "Maps · Mobile",
    color: "var(--viz-series-2)",
  },
  {
    key: "impressions_search_desktop",
    label: "Search · Desktop",
    color: "var(--viz-series-1)",
  },
  {
    key: "impressions_search_mobile",
    label: "Search · Mobile",
    color: "var(--viz-series-2)",
  },
];

/**
 * Impressions are shown as two facets on one shared scale rather than four mixed
 * lines: surface is the facet, device is the colour. Two hues do the whole job.
 */
export const IMPRESSION_FACETS: {
  id: string;
  label: string;
  series: SeriesSpec<ImpressionMetricKey>[];
}[] = [
  {
    id: "maps",
    label: "Google Maps",
    series: [
      {
        key: "impressions_maps_desktop",
        label: "Desktop",
        color: "var(--viz-series-1)",
      },
      {
        key: "impressions_maps_mobile",
        label: "Mobile",
        color: "var(--viz-series-2)",
      },
    ],
  },
  {
    id: "search",
    label: "Google Search",
    series: [
      {
        key: "impressions_search_desktop",
        label: "Desktop",
        color: "var(--viz-series-1)",
      },
      {
        key: "impressions_search_mobile",
        label: "Mobile",
        color: "var(--viz-series-2)",
      },
    ],
  },
];

export const IMPRESSION_DEVICE_KEYS: SeriesSpec<string>[] = [
  { key: "desktop", label: "Desktop", color: "var(--viz-series-1)" },
  { key: "mobile", label: "Mobile", color: "var(--viz-series-2)" },
];

/** An absent value is an absent value; it is never coerced into a number. */
export function metricValue(point: PerformancePoint, key: string): number | null {
  const value = (point as unknown as Record<string, number | null | undefined>)[key];
  return typeof value === "number" ? value : null;
}

export function hasAnyValue(points: PerformancePoint[], key: string) {
  return points.some((point) => metricValue(point, key) !== null);
}

/** Full precision, grouped — for tables, tooltips and anywhere a figure is read exactly. */
export function formatExact(value: number | null | undefined) {
  return typeof value === "number" ? value.toLocaleString("en") : null;
}

/**
 * Headline figures stay exact while they are short enough to read, and compact
 * beyond that. Large standalone numbers keep proportional figures.
 */
export function formatHeadline(value: number | null | undefined) {
  if (typeof value !== "number") return null;
  if (Math.abs(value) < 10_000) return value.toLocaleString("en");
  return new Intl.NumberFormat("en", {
    notation: "compact",
    compactDisplay: "short",
    maximumFractionDigits: 1,
  }).format(value);
}

/** Axis ticks are compact so they never collide at phone width. */
export function formatAxisNumber(value: number) {
  if (Math.abs(value) < 1_000) return String(value);
  return new Intl.NumberFormat("en", {
    notation: "compact",
    compactDisplay: "short",
    maximumFractionDigits: 1,
  }).format(value);
}

function toDate(value: string) {
  const parsed = parseISO(value);
  return isValid(parsed) ? parsed : null;
}

/** "12 Sep" for an axis tick; the raw value when it cannot be parsed. */
export function formatAxisDate(value: string) {
  const date = toDate(value);
  return date ? format(date, "d MMM") : value;
}

/** "12 Sep 2026" for a tooltip heading or a table cell. */
export function formatPointDate(value: string) {
  const date = toDate(value);
  return date ? format(date, "d MMM yyyy") : value;
}

/** "September 2026" from a `YYYY-MM` reporting month. */
export function formatReportingMonth(value: string) {
  const date = toDate(`${value}-01`);
  return date ? format(date, "MMMM yyyy") : value;
}

/** Rounds an axis maximum up to a readable number so both facets share clean ticks. */
export function niceCeiling(value: number) {
  if (!Number.isFinite(value) || value <= 0) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const steps = [1, 2, 2.5, 5, 10];
  const step = steps.find((candidate) => value <= candidate * magnitude) ?? 10;
  return step * magnitude;
}
