"use client";

import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRoot,
  TableRow,
} from "@/components/tailgrids/core/table";
import type { RankPoint } from "@/services/api/market";
import { Link1AngularRight } from "@tailgrids/icons";
import { formatWeekLong, isNotFound, localPackLabel, NOT_FOUND_LABEL } from "./rank-format";

/**
 * The table twin of the chart: every value the chart plots is readable here without
 * relying on colour, hover, or the ability to see the marks at all.
 */
export function RankHistoryTable({ points }: { points: RankPoint[] }) {
  const newestFirst = [...points].reverse();

  return (
    <TableRoot>
      <caption className="sr-only">
        Weekly search position and local pack position, newest week first.
      </caption>
      <TableHeader>
        <TableRow>
          <TableHead scope="col">Week</TableHead>
          <TableHead scope="col">Position</TableHead>
          <TableHead scope="col">Local pack</TableHead>
          <TableHead scope="col">Result</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {newestFirst.map((point) => (
          <TableRow key={point.week_start}>
            <TableCell className="whitespace-nowrap text-text-secondary">
              {formatWeekLong(point.week_start)}
            </TableCell>
            <TableCell className="whitespace-nowrap text-text-primary tabular-nums">
              {isNotFound(point) ? NOT_FOUND_LABEL : `#${point.rank_absolute}`}
            </TableCell>
            <TableCell className="whitespace-nowrap text-text-secondary tabular-nums">
              {localPackLabel(point.rank_in_local_pack)}
            </TableCell>
            <TableCell>
              {point.result_url ? (
                <a href={point.result_url} target="_blank" rel="noreferrer noopener" className="inline-flex min-h-11 items-center gap-1 text-sm font-medium text-text-secondary hover:text-text-primary hover:underline">
                  Open result <Link1AngularRight aria-hidden="true" className="size-3.5" />
                </a>
              ) : <span className="text-text-disable">—</span>}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </TableRoot>
  );
}
