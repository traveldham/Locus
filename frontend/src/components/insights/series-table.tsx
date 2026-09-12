"use client";

import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRoot,
  TableRow,
} from "@/components/tailgrids/core/table";
import type { PerformancePoint } from "@/services/api/insights";
import { formatExact, formatPointDate, metricValue, type SeriesSpec } from "./chart-series";

interface SeriesTableProps {
  points: PerformancePoint[];
  series: SeriesSpec<string>[];
  caption: string;
}

/**
 * The chart's table twin. Every plotted value is readable here without hovering,
 * and an absent day says so in words rather than showing a zero.
 */
export function SeriesTable({ points, series, caption }: SeriesTableProps) {
  return (
    <div
      role="region"
      aria-label={caption}
      tabIndex={0}
      className="max-h-96 overflow-y-auto rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-primary-500"
    >
      <TableRoot className="text-sm">
        <caption className="sr-only">{caption}</caption>
        <TableHeader>
          <TableRow>
            <TableHead className="text-left whitespace-nowrap">Date</TableHead>
            {series.map((spec) => (
              <TableHead key={spec.key} className="text-right whitespace-nowrap">
                {spec.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {points.map((point) => (
            <TableRow key={point.date}>
              <TableCell className="whitespace-nowrap text-text-primary">
                {formatPointDate(point.date)}
              </TableCell>
              {series.map((spec) => {
                const value = formatExact(metricValue(point, spec.key));
                return (
                  <TableCell
                    key={spec.key}
                    className="text-right tabular-nums whitespace-nowrap"
                  >
                    {value ?? <span className="text-text-disable">Not reported</span>}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </TableRoot>
    </div>
  );
}
