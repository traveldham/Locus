import { cn } from "@/utils/cn";
import { StarIcon } from "@tailgrids/icons";

const STAR_POSITIONS = [1, 2, 3, 4, 5];

const STAR_SIZES = {
  sm: "size-3.5",
  md: "size-4",
} as const;

export interface StarRatingProps {
  /** Whole stars, 1 through 5, exactly as Google returned them. */
  rating: number;
  size?: keyof typeof STAR_SIZES;
  /** Render the number beside the stars so the value never rests on colour alone. */
  showValue?: boolean;
  className?: string;
}

/**
 * The glyphs are decorative: the rating is announced through the label, and the
 * optional numeral repeats it in text for anyone who cannot separate the two fills.
 */
export function StarRating({ rating, size = "md", showValue = false, className }: StarRatingProps) {
  const filled = Math.min(5, Math.max(0, Math.round(rating)));

  return (
    <span
      role="img"
      aria-label={`${filled} out of 5 stars`}
      className={cn("inline-flex items-center gap-1.5", className)}
    >
      <span aria-hidden="true" className="inline-flex items-center gap-0.5">
        {STAR_POSITIONS.map((position) => (
          <StarIcon
            key={position}
            focusable="false"
            className={cn(
              "shrink-0",
              STAR_SIZES[size],
              position <= filled ? "text-badge-warning-icon-color" : "text-border-secondary-alt",
            )}
          />
        ))}
      </span>
      {showValue ? (
        <span
          aria-hidden="true"
          className="text-xs font-semibold text-text-secondary tabular-nums"
        >
          {filled}
        </span>
      ) : null}
    </span>
  );
}
