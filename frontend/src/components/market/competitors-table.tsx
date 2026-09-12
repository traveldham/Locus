"use client";

import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRoot,
  TableRow,
} from "@/components/tailgrids/core/table";
import type { Competitor } from "@/services/api/market";

/** Used wherever the API returned no value — never a zero, never a blank. */
function NotReported() {
  return (
    <span className="text-text-tertiary">
      <span aria-hidden="true">—</span>
      <span className="sr-only">Not reported</span>
    </span>
  );
}

function ClaimedChip({ isClaimed }: { isClaimed: boolean }) {
  return (
    <span
      className={
        isClaimed
          ? "inline-flex items-center gap-1.5 rounded-full bg-badge-success-background px-2.5 py-1 text-xs leading-4 font-medium whitespace-nowrap text-badge-success-text"
          : "inline-flex items-center gap-1.5 rounded-full bg-badge-neutral-background px-2.5 py-1 text-xs leading-4 font-medium whitespace-nowrap text-badge-neutral-text"
      }
    >
      <span
        aria-hidden="true"
        className={
          isClaimed
            ? "size-1.5 rounded-full bg-badge-success-icon-color"
            : "size-1.5 rounded-full bg-badge-neutral-icon-color"
        }
      />
      {isClaimed ? "Claimed" : "Unclaimed"}
    </span>
  );
}

/**
 * The rank gap is the only comparison drawn here, because the rank of this business
 * is the only one of its own numbers the API returned for this week. Review counts,
 * ratings and photo counts are shown as the competitor's own figures, never as a
 * difference against a number nobody supplied.
 */
function rankGapLabel(competitorRank: number, yourRank: number) {
  const gap = yourRank - competitorRank;
  if (gap === 0) return "Level with you";
  if (gap > 0) return `${gap} ahead of you`;
  return `${Math.abs(gap)} behind you`;
}

export interface CompetitorsTableProps {
  competitors: Competitor[];
  /** This business's own position that same week, from the rankings endpoint. */
  yourRank: number | null;
}

export function CompetitorsTable({ competitors, yourRank }: CompetitorsTableProps) {
  const ordered = [...competitors].sort((a, b) => {
    if (a.rank_absolute === null) return b.rank_absolute === null ? 0 : 1;
    if (b.rank_absolute === null) return -1;
    return a.rank_absolute - b.rank_absolute;
  });

  return (
    <TableRoot>
      <caption className="sr-only">
        Businesses ranking for this keyword, best position first.
      </caption>
      <TableHeader>
        <TableRow>
          <TableHead scope="col">Business</TableHead>
          <TableHead scope="col">Rank</TableHead>
          {yourRank !== null ? <TableHead scope="col">Versus you</TableHead> : null}
          <TableHead scope="col" className="text-right">
            Reviews
          </TableHead>
          <TableHead scope="col" className="text-right">
            Rating
          </TableHead>
          <TableHead scope="col" className="text-right">
            Photos
          </TableHead>
          <TableHead scope="col">Profile</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {ordered.map((competitor) => (
          <TableRow key={competitor.competitor_place_id}>
            <TableCell className="text-text-primary">
              <span className="block max-w-56 truncate" title={competitor.competitor_name}>
                {competitor.competitor_name}
              </span>
            </TableCell>
            <TableCell className="whitespace-nowrap text-text-primary tabular-nums">
              {competitor.rank_absolute === null ? (
                <NotReported />
              ) : (
                `#${competitor.rank_absolute}`
              )}
            </TableCell>
            {yourRank !== null ? (
              <TableCell className="whitespace-nowrap text-text-secondary">
                {competitor.rank_absolute === null ? (
                  <NotReported />
                ) : (
                  rankGapLabel(competitor.rank_absolute, yourRank)
                )}
              </TableCell>
            ) : null}
            <TableCell className="text-right text-text-secondary tabular-nums">
              {competitor.review_count === null ? (
                <NotReported />
              ) : (
                competitor.review_count.toLocaleString()
              )}
            </TableCell>
            <TableCell className="text-right text-text-secondary tabular-nums">
              {competitor.average_rating === null ? (
                <NotReported />
              ) : (
                competitor.average_rating.toFixed(1)
              )}
            </TableCell>
            <TableCell className="text-right text-text-secondary tabular-nums">
              {competitor.photo_count === null ? (
                <NotReported />
              ) : (
                competitor.photo_count.toLocaleString()
              )}
            </TableCell>
            <TableCell>
              <ClaimedChip isClaimed={competitor.is_claimed} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </TableRoot>
  );
}
