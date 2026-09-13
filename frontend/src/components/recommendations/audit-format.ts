import type { HealthScore, Severity } from "@/services/api/recommendations";

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
