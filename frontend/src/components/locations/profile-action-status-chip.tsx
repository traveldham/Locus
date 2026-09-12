import type { ProfileActionStatus } from "@/services/api/locations";
import { cn } from "@/utils/cn";

type StatusTone = "neutral" | "primary" | "success" | "error";

const TONE_SURFACE: Record<StatusTone, string> = {
  neutral: "bg-badge-neutral-background text-badge-neutral-text",
  primary: "bg-badge-primary-background text-badge-primary-text",
  success: "bg-badge-success-background text-badge-success-text",
  error: "bg-badge-error-background text-badge-error-text",
};

const TONE_MARKER: Record<StatusTone, string> = {
  neutral: "bg-badge-neutral-icon-color",
  primary: "bg-badge-primary-icon-color",
  success: "bg-badge-success-icon-color",
  error: "bg-badge-error-icon-color",
};

const STATUS_DEFINITIONS: Record<ProfileActionStatus, { label: string; tone: StatusTone }> = {
  pending: { label: "Pending", tone: "neutral" },
  approved: { label: "Approved", tone: "primary" },
  executing: { label: "Sending to Google", tone: "primary" },
  succeeded: { label: "Applied", tone: "success" },
  failed: { label: "Failed", tone: "error" },
};

/**
 * The outcome of one audited action. The label always carries the meaning, so the
 * coloured marker beside it is decorative.
 */
export function ProfileActionStatusChip({
  status,
  className,
}: {
  status: ProfileActionStatus;
  className?: string;
}) {
  const definition = STATUS_DEFINITIONS[status];
  if (!definition) return null;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs leading-4 font-medium whitespace-nowrap",
        TONE_SURFACE[definition.tone],
        className,
      )}
    >
      <span
        aria-hidden="true"
        className={cn("size-1.5 shrink-0 rounded-full", TONE_MARKER[definition.tone])}
      />
      {definition.label}
    </span>
  );
}
