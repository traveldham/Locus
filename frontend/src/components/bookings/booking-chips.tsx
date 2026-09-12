import {
  bookingSourceLabel,
  bookingStatusLabel,
  type BookingSource,
  type BookingStatus,
} from "@/services/api/bookings";
import { cn } from "@/utils/cn";

/**
 * Only tokens defined in both themes are used, and the written label always carries
 * the meaning — the colour and the dot are reinforcement, never the message.
 */
const STATUS_STYLES: Record<BookingStatus, { chip: string; dot: string }> = {
  new: {
    chip: "bg-badge-primary-background text-badge-primary-text",
    dot: "bg-badge-primary-icon-color",
  },
  confirmed: {
    chip: "bg-badge-blue-background text-badge-blue-text",
    dot: "bg-badge-blue-icon-color",
  },
  completed: {
    chip: "bg-badge-success-background text-badge-success-text",
    dot: "bg-badge-success-icon-color",
  },
  cancelled: {
    chip: "bg-badge-neutral-background text-badge-neutral-text",
    dot: "bg-badge-neutral-icon-color",
  },
  no_show: {
    chip: "bg-badge-error-background text-badge-error-text",
    dot: "bg-badge-error-icon-color",
  },
};

const CHIP_BASE =
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs leading-4 font-medium whitespace-nowrap";

export function BookingStatusChip({ status }: { status: BookingStatus }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.cancelled;

  return (
    <span className={cn(CHIP_BASE, style.chip)}>
      <span aria-hidden="true" className={cn("size-1.5 shrink-0 rounded-full", style.dot)} />
      {bookingStatusLabel(status)}
    </span>
  );
}

/**
 * `google_profile` is the one source the product exists to prove, so it is the only
 * one that carries emphasis. No Google glyph appears here: the booking record itself
 * is Locus data, and the section mark says so — the glyph would contradict it.
 */
export function BookingSourceChip({ source }: { source: BookingSource }) {
  const isGoogle = source === "google_profile";

  return (
    <span
      className={cn(
        CHIP_BASE,
        isGoogle
          ? "bg-badge-violet-background text-badge-violet-text"
          : "bg-badge-gray-background text-text-secondary",
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "size-1.5 shrink-0 rounded-full",
          isGoogle ? "bg-badge-violet-icon-color" : "bg-badge-gray-icon",
        )}
      />
      {bookingSourceLabel(source)}
      {isGoogle ? (
        <span className="sr-only"> — attributable to your Google Business Profile</span>
      ) : null}
    </span>
  );
}
