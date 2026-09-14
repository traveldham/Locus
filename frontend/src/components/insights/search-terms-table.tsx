"use client";

import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRoot,
  TableRow,
} from "@/components/tailgrids/core/table";
import type { SearchTerm } from "@/services/api/insights";
import { InfoCircle } from "@tailgrids/icons";
import { formatExact, formatReportingMonth } from "./chart-series";

/**
 * Renders one impression figure.
 *
 * Google withholds the exact count for low-volume terms and returns a threshold
 * instead. Printing that threshold as if it were the count would invent precision
 * Google never gave, so a withheld figure is always shown as a "fewer than" bound.
 */
function Impressions({ term }: { term: SearchTerm }) {
  const exact = formatExact(term.impressions);

  if (term.is_threshold) {
    return (
      <span className="inline-flex items-center justify-end gap-1.5 text-text-secondary">
        <InfoCircle
          aria-hidden="true"
          focusable="false"
          className="size-3.5 shrink-0 text-icon-tertiary"
        />
        {exact === null ? (
          <span>Below threshold</span>
        ) : (
          <span className="tabular-nums">
            &lt; {exact}
            <span className="sr-only">
              {" "}
              — fewer than {exact}; Google withheld the exact count
            </span>
          </span>
        )}
      </span>
    );
  }

  if (exact === null) return <span className="text-text-disable">Not reported</span>;
  return <span className="tabular-nums text-text-primary">{exact}</span>;
}

interface SearchTermsTableProps {
  items: SearchTerm[];
  /** True when the month filter is set, so the repeated month column can be dropped. */
  hideMonth?: boolean;
  /** True when the page is already filtered to one location. */
  hideLocation?: boolean;
}

export function SearchTermsTable({
  items,
  hideMonth = false,
  hideLocation = false,
}: SearchTermsTableProps) {
  return (
    <TableRoot className="text-sm">
      <caption className="sr-only">
        Search terms that led people to your profile, most impressions first
      </caption>
      <TableHeader>
        <TableRow>
          <TableHead className="text-left">Search term</TableHead>
          {hideLocation ? null : <TableHead className="text-left">Profile</TableHead>}
          {hideMonth ? null : (
            <TableHead className="text-left whitespace-nowrap">Month</TableHead>
          )}
          <TableHead className="text-right whitespace-nowrap">Impressions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((term) => (
          <TableRow key={`${term.year_month}-${term.search_term}`}>
            <TableCell className="text-text-primary">{term.search_term}</TableCell>
            {hideLocation ? null : (
              <TableCell className="text-text-secondary">
                {term.location_title ?? term.location_id}
              </TableCell>
            )}
            {hideMonth ? null : (
              <TableCell className="whitespace-nowrap text-text-tertiary">
                {formatReportingMonth(term.year_month)}
              </TableCell>
            )}
            <TableCell className="text-right whitespace-nowrap">
              <Impressions term={term} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </TableRoot>
  );
}
