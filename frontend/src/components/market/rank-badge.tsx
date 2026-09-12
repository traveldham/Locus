import { cn } from "@/utils/cn";
import { formatRank } from "./rank-format";

/**
 * A position, or the fact that the business was not found at all. The two read
 * differently on purpose — "not found" is a result, not a missing number — and the
 * wording carries the meaning, so nothing depends on colour.
 */
export function RankBadge({
  rank,
  className,
}: {
  rank: number | null;
  className?: string;
}) {
  const notFound = rank === null;

  return (
    <span
      className={cn(
        "inline-flex min-w-11 items-center justify-center rounded-md px-2 py-1 text-sm leading-5 font-semibold whitespace-nowrap tabular-nums",
        notFound
          ? "bg-badge-neutral-background text-badge-neutral-text"
          : "bg-badge-primary-background text-badge-primary-text",
        className,
      )}
    >
      {formatRank(rank)}
      <span className="sr-only">
        {notFound ? "" : " position in the search results"}
      </span>
    </span>
  );
}
