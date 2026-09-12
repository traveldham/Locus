import type { LocationSummary } from "@/services/api/locations";
import { cn } from "@/utils/cn";

export type LocationStatusKind =
  | "sample_data"
  | "open"
  | "closed_temporarily"
  | "closed_permanently"
  | "open_status_unknown"
  | "verified"
  | "not_verified"
  | "pending_edits"
  | "no_pending_edits"
  | "google_updated"
  | "no_google_updates"
  | "duplicate"
  | "not_duplicate";

type StatusTone = "positive" | "caution" | "critical" | "info" | "neutral";

const TONE_SURFACE: Record<StatusTone, string> = {
  positive: "bg-badge-success-background text-badge-success-text",
  caution: "bg-badge-warning-background text-badge-warning-text",
  critical: "bg-badge-error-background text-badge-error-text",
  info: "bg-badge-sky-background text-badge-sky-text",
  neutral: "bg-badge-neutral-background text-badge-neutral-text",
};

const TONE_MARKER: Record<StatusTone, string> = {
  positive: "bg-badge-success-icon-color",
  caution: "bg-badge-warning-icon-color",
  critical: "bg-badge-error-icon-color",
  info: "bg-badge-sky-icon-color",
  neutral: "bg-badge-neutral-icon-color",
};

const STATUS_DEFINITIONS: Record<LocationStatusKind, { label: string; tone: StatusTone }> = {
  sample_data: { label: "Sample data", tone: "info" },
  open: { label: "Open", tone: "positive" },
  closed_temporarily: { label: "Temporarily closed", tone: "caution" },
  closed_permanently: { label: "Permanently closed", tone: "critical" },
  open_status_unknown: { label: "Open status not set", tone: "neutral" },
  verified: { label: "Verified", tone: "positive" },
  not_verified: { label: "Not verified", tone: "caution" },
  pending_edits: { label: "Pending edits", tone: "info" },
  no_pending_edits: { label: "No pending edits", tone: "neutral" },
  google_updated: { label: "Google suggested an update", tone: "info" },
  no_google_updates: { label: "No suggested updates", tone: "neutral" },
  duplicate: { label: "Duplicate", tone: "critical" },
  not_duplicate: { label: "Not a duplicate", tone: "neutral" },
};

export interface LocationStatusChipProps {
  kind: LocationStatusKind;
  className?: string;
}

/**
 * Status is always carried by the label text; the coloured marker is decorative,
 * so the meaning never depends on colour alone.
 */
export function LocationStatusChip({ kind, className }: LocationStatusChipProps) {
  const { label, tone } = STATUS_DEFINITIONS[kind];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs leading-4 font-medium whitespace-nowrap",
        TONE_SURFACE[tone],
        className,
      )}
    >
      <span aria-hidden="true" className={cn("size-1.5 shrink-0 rounded-full", TONE_MARKER[tone])} />
      {label}
    </span>
  );
}

type LocationStatusSource = Pick<
  LocationSummary,
  | "source"
  | "open_status"
  | "has_voice_of_merchant"
  | "has_pending_edits"
  | "has_google_updated"
  | "is_duplicate"
>;

/**
 * The statuses worth surfacing in a dense list: the open status plus any Google-side
 * state that needs a person to look at it. "Verified" is opt-in because it is the
 * expected state and would otherwise repeat on every row.
 *
 * "Sample data" is never opt-in. A profile served from the sample dataset says so on
 * every row and every header, so it cannot be read as the business's own Google data.
 */
export function locationStatusKinds(
  location: LocationStatusSource,
  { includeVerified = false }: { includeVerified?: boolean } = {},
): LocationStatusKind[] {
  const kinds: LocationStatusKind[] = [];

  if (location.source === "fixture") kinds.push("sample_data");
  kinds.push(location.open_status ?? "open_status_unknown");

  if (!location.has_voice_of_merchant) kinds.push("not_verified");
  else if (includeVerified) kinds.push("verified");

  if (location.has_pending_edits) kinds.push("pending_edits");
  if (location.has_google_updated) kinds.push("google_updated");
  if (location.is_duplicate) kinds.push("duplicate");

  return kinds;
}
