import type {
  HealthScore,
  LocationMetric,
  Severity,
} from "@/services/api/recommendations";

export const SEVERITY_ORDER: Severity[] = ["critical", "warning", "notice"];

export const SEVERITY_COLOR: Record<Severity, "error" | "warning" | "gray"> = {
  critical: "error",
  warning: "warning",
  notice: "gray",
};

/** One sentence per severity, so the bands are never left to the reader to guess. */
export const SEVERITY_HINT: Record<Severity, string> = {
  critical: "Directly observed and customer-facing. Work these first.",
  warning: "A measured gap worth scheduling once the critical work is clear.",
  notice: "Small or optional. Confirm before acting.",
};

/** Column headings in the dense fleet table, where the full label will not fit. */
export const SHORT_CATEGORY: Record<string, string> = {
  profile: "Profile",
  reputation: "Reviews",
  visibility: "Visibility",
  operations: "Ops",
  performance: "Perf",
  content: "Content",
};

export const GRADE_LABEL: Record<HealthScore["grade"], string> = {
  excellent: "Excellent",
  good: "Good",
  fair: "Fair",
  poor: "Poor",
  not_evaluated: "Not evaluated",
};

/** Scores share one colour scale everywhere they appear. */
export function scoreTone(
  score: number | null,
): "success" | "warning" | "error" | "muted" {
  if (score === null) return "muted";
  if (score >= 75) return "success";
  if (score >= 50) return "warning";
  return "error";
}

export const TONE_TEXT = {
  success: "text-badge-success-text",
  warning: "text-badge-warning-text",
  error: "text-badge-error-text",
  muted: "text-text-disable",
} as const;

export const TONE_FILL = {
  success: "bg-badge-success-text",
  warning: "bg-badge-warning-text",
  error: "bg-badge-error-text",
  muted: "bg-text-disable",
} as const;

export const TONE_STROKE = {
  success: "stroke-badge-success-text",
  warning: "stroke-badge-warning-text",
  error: "stroke-badge-error-text",
  muted: "stroke-text-disable",
} as const;

export function formatMetric(metric: LocationMetric): string {
  if (!metric.available || metric.value === null) return "Not reported";
  const value = metric.value;
  switch (metric.unit) {
    case "percent":
      return `${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}%`;
    case "rating":
      return `${value.toFixed(2)} ★`;
    case "days":
      return `${value.toLocaleString()} ${value === 1 ? "day" : "days"}`;
    case "rank":
      return `#${value.toLocaleString(undefined, { maximumFractionDigits: 1 })}`;
    default:
      return value.toLocaleString();
  }
}

/** A change is only good or bad once you know which way the metric should move. */
export function changeTone(
  metric: LocationMetric,
): "success" | "error" | "muted" {
  if (metric.change_pct === null || metric.direction === "neutral")
    return "muted";
  const rising = metric.change_pct > 0;
  const good = metric.direction === "up_is_good" ? rising : !rising;
  if (metric.change_pct === 0) return "muted";
  return good ? "success" : "error";
}

export function formatChange(change: number | null): string | null {
  if (change === null) return null;
  return `${change > 0 ? "+" : ""}${(change * 100).toFixed(1)}%`;
}

export function formatSigned(value: number | null | undefined): string | null {
  if (value === null || value === undefined || value === 0) return null;
  return `${value > 0 ? "+" : ""}${value}`;
}
