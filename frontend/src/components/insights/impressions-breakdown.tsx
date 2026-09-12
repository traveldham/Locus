"use client";

import {
  IMPRESSION_METRIC_KEYS,
  type DataSource,
  type PerformancePoint,
} from "@/services/api/insights";
import { LaptopPhone } from "@tailgrids/icons";
import { useMemo } from "react";
import { ChartCard } from "./chart-card";
import { ChartLegend } from "./chart-legend";
import {
  IMPRESSION_DEVICE_KEYS,
  IMPRESSION_FACETS,
  IMPRESSION_SERIES,
  metricValue,
  niceCeiling,
} from "./chart-series";
import { MetricTile } from "./metric-tile";
import { SeriesTable } from "./series-table";
import { sourceProvenance } from "./source-provenance";
import { TimeSeriesChart } from "./time-series-chart";

interface ImpressionsBreakdownProps {
  points: PerformancePoint[];
  totals: Record<string, number>;
  source: DataSource;
  isRefetching: boolean;
}

/**
 * Impressions split by surface and device.
 *
 * Google reports these four separately because a Maps impression on a phone is a
 * different thing from a Search impression on a desktop, so they are never merged
 * into one line. Surface becomes the facet, device becomes the colour, and both
 * facets share one y-axis so they can be compared directly.
 */
export function ImpressionsBreakdown({
  points,
  totals,
  source,
  isRefetching,
}: ImpressionsBreakdownProps) {
  const sharedMax = useMemo(() => {
    let max = 0;
    for (const point of points) {
      for (const key of IMPRESSION_METRIC_KEYS) {
        const value = metricValue(point, key);
        if (value !== null && value > max) max = value;
      }
    }
    return max > 0 ? niceCeiling(max) : undefined;
  }, [points]);

  const hasAnyImpression = sharedMax !== undefined;

  const totalsGrid = (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      {IMPRESSION_SERIES.map((spec) => (
        <MetricTile
          key={spec.key}
          label={spec.label}
          value={typeof totals[spec.key] === "number" ? totals[spec.key] : null}
          hint="Impressions in this range"
        />
      ))}
    </div>
  );

  return (
    <ChartCard
      title="Impressions by surface and device"
      icon={<LaptopPhone aria-hidden="true" focusable="false" />}
      description="Where your profile was seen, kept split four ways. Maps and Search are plotted on the same scale, so the two can be read against each other."
      isRefetching={isRefetching}
      note={
        <>
          A break in a line is a day Google reported no value for that surface and device,
          which is not the same as nobody seeing the profile. Figures{" "}
          {sourceProvenance(source)}.
        </>
      }
      chart={
        <div className="flex flex-col gap-5">
          {totalsGrid}
          {hasAnyImpression ? (
            <>
              <ChartLegend items={IMPRESSION_DEVICE_KEYS} label="Device" />
              <div className="grid gap-5 xl:grid-cols-2">
                {IMPRESSION_FACETS.map((facet) => (
                  <div key={facet.id} className="min-w-0">
                    <h3 className="mb-2 text-sm font-semibold text-text-primary">
                      {facet.label}
                    </h3>
                    <TimeSeriesChart
                      points={points}
                      series={facet.series}
                      yMax={sharedMax}
                      height={240}
                      description={`Daily ${facet.label} impressions on desktop and mobile, on the same scale as the other surface. The same figures are in the table view.`}
                    />
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="rounded-lg border border-dashed border-card-border px-4 py-10 text-center text-sm text-text-tertiary">
              Google reported no impressions for this range.
            </p>
          )}
        </div>
      }
      table={
        <div className="flex flex-col gap-5">
          {totalsGrid}
          <SeriesTable
            points={points}
            series={IMPRESSION_SERIES}
            caption="Impressions by surface and device, by day"
          />
        </div>
      }
    />
  );
}
