import { cn } from "@/utils/cn";
import { Google } from "@tailgrids/icons";
import Image from "next/image";

/**
 * Where the data on a surface comes from.
 *
 * Google supplies locations, hours, reviews and performance. It supplies nothing at
 * all for keyword rankings, competitors or individual bookings — those come from
 * Locus. Without a mark a reader reasonably assumes everything on screen is Google's,
 * and then asks why it does not match their Google dashboard. It never will.
 *
 * This is deliberately separate from any "sample data" indicator: that one answers
 * "is this real yet" and goes away, this one answers "where would this come from"
 * and is true forever.
 */
export type MarkSource = "google" | "locus";

const COPY: Record<MarkSource, { label: string; detail: string }> = {
  google: {
    label: "Google data",
    detail: "Supplied by the Google Business Profile API.",
  },
  locus: {
    label: "Locus data",
    detail:
      "Measured by Locus, not supplied by Google. Google publishes no ranking, competitor or individual booking data, so these figures will not match a Google dashboard.",
  },
};

// The favicon is a dark maroon glyph on transparent, so it disappears on the dark
// theme's surfaces. Dark mode is the `[data-theme="dark"]` attribute, so the invert
// is scoped to that attribute rather than a colour-scheme media query.
const invertOnDarkTheme = "[[data-theme=dark]_&]:brightness-0 [[data-theme=dark]_&]:invert";

export interface SourceMarkProps {
  source: MarkSource;
  /**
   * Extra context appended to the accessible description — for example which figures
   * on the section the mark covers.
   */
  detail?: string;
  className?: string;
}

export function SourceMark({ source, detail, className }: SourceMarkProps) {
  const copy = COPY[source];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-card-border bg-background-gray-secondary px-2.5 py-1 text-xs leading-4 font-medium whitespace-nowrap text-text-secondary",
        className,
      )}
    >
      {source === "locus" ? (
        <Image
          src="/brand/favicon.webp"
          alt=""
          width={180}
          height={180}
          aria-hidden="true"
          className={cn("size-3.5 shrink-0 object-contain", invertOnDarkTheme)}
        />
      ) : (
        <Google
          aria-hidden="true"
          focusable="false"
          className="size-3.5 shrink-0 text-icon-secondary"
        />
      )}
      {copy.label}
      <span className="sr-only">
        . {copy.detail}
        {detail ? ` ${detail}` : ""}
      </span>
    </span>
  );
}
