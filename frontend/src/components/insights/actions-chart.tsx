"use client";

import type { DataSource, PerformancePoint } from "@/services/api/insights";
import { TrendUp2 } from "@tailgrids/icons";
import { useMemo, useState } from "react";
import { ChartCard } from "./chart-card";
import { ChartLegend, type ChartLegendItem } from "./chart-legend";
import { ACTION_SERIES, hasAnyValue } from "./chart-series";
import { SeriesTable } from "./series-table";
import { sourceProvenance } from "./source-provenance";
import { TimeSeriesChart } from "./time-series-chart";

interface ActionsChartProps {
  points: PerformancePoint[];
  source: DataSource;
  isRefetching: boolean;
}

/**
 * What customers did after finding the profile, day by day.
 *
 * All five metrics are counts of the same kind of event, so they share one axis —
 * there is never a second y-scale.
 */
export function ActionsChart({ points, source, isRefetching }: ActionsChartProps) {
  const [hiddenKeys, setHiddenKeys] = useState<string[]>([]);

  const availability = useMemo(() => {
    const map = new Map<string, boolean>();
    for (const spec of ACTION_SERIES) map.set(spec.key, hasAnyValue(points, spec.key));
    return map;
  }, [points]);

  const visibleSeries = useMemo(
    () =>
      ACTION_SERIES.filter(
        (spec) => availability.get(spec.key) && !hiddenKeys.includes(spec.key),
      ),
    [availability, hiddenKeys],
  );

  const legendItems: ChartLegendItem[] = ACTION_SERIES.map((spec) => ({
    key: spec.key,
    label: spec.label,
    color: spec.color,
    isHidden: hiddenKeys.includes(spec.key),
    isUnavailable: !availability.get(spec.key),
  }));

  function toggle(key: string) {
    setHiddenKeys((current) =>
      current.includes(key) ? current.filter((item) => item !== key) : [...current, key],
    );
  }

  return (
    <ChartCard
      title="Customer actions"
      icon={<TrendUp2 aria-hidden="true" focusable="false" />}
      description="Every action Google attributes to your profile, one line per action type on a single shared scale."
      isRefetching={isRefetching}
      note={
        <>
          A break in a line is a day Google reported no value for that action. It is an
          absence, not a zero, so the line stops rather than dropping to the baseline; a day
          that stands alone between two absences is drawn as a single dot. Figures{" "}
          {sourceProvenance(source)}.
        </>
      }
      chart={
        <div className="flex flex-col gap-4">
          <ChartLegend items={legendItems} label="Action metrics shown" onToggle={toggle} />
          {visibleSeries.length === 0 ? (
            <p className="rounded-lg border border-dashed border-card-border px-4 py-10 text-center text-sm text-text-tertiary">
              {legendItems.every((item) => item.isUnavailable)
                ? "Google reported no customer actions for this range."
                : "Every action is hidden. Turn one back on to plot it."}
            </p>
          ) : (
            <TimeSeriesChart
              points={points}
              series={visibleSeries}
              height={280}
              description={`Daily totals for ${visibleSeries
                .map((spec) => spec.label)
                .join(", ")}. The same figures are in the table view.`}
            />
          )}
        </div>
      }
      table={
        <SeriesTable
          points={points}
          series={ACTION_SERIES}
          caption="Customer actions by day"
        />
      }
    />
  );
}
