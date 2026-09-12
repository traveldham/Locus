"use client";

import type { PerformancePoint } from "@/services/api/insights";
import { useMemo } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  formatAxisDate,
  formatAxisNumber,
  formatExact,
  formatPointDate,
  metricValue,
  type SeriesSpec,
} from "./chart-series";

interface TimeSeriesChartProps {
  points: PerformancePoint[];
  series: SeriesSpec<string>[];
  /**
   * Shared upper bound. Facets of one measure pass the same value so the two plots
   * can be compared by eye; a lone chart leaves it out and lets the axis fit.
   */
  yMax?: number;
  height?: number;
  /** Describes the plot for screen readers before the interactive layer is reached. */
  description: string;
}

/**
 * One measure over time.
 *
 * `null` is rendered as a gap, never as zero: Recharts is left on its default
 * `connectNulls={false}`, and a day that survives alone between two absences gets
 * an explicit dot so a single reported value is never invisible.
 */
export function TimeSeriesChart({
  points,
  series,
  yMax,
  height = 260,
  description,
}: TimeSeriesChartProps) {
  const pointsByDate = useMemo(() => {
    const map = new Map<string, PerformancePoint>();
    for (const point of points) map.set(point.date, point);
    return map;
  }, [points]);

  /** Indexes whose neighbours are both absent, per series. */
  const isolatedIndexes = useMemo(() => {
    const map = new Map<string, Set<number>>();
    for (const spec of series) {
      const isolated = new Set<number>();
      points.forEach((point, index) => {
        if (metricValue(point, spec.key) === null) return;
        const before = index > 0 ? metricValue(points[index - 1], spec.key) : null;
        const after =
          index < points.length - 1 ? metricValue(points[index + 1], spec.key) : null;
        if (before === null && after === null) isolated.add(index);
      });
      map.set(spec.key, isolated);
    }
    return map;
  }, [points, series]);

  return (
    <>
      <p className="sr-only">{description}</p>
      <div style={{ height }} className="w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={points} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
            <CartesianGrid vertical={false} stroke="var(--viz-grid)" strokeWidth={1} />
            <XAxis
              dataKey="date"
              tickFormatter={formatAxisDate}
              tickLine={false}
              axisLine={{ stroke: "var(--viz-grid)" }}
              tick={{ fill: "var(--viz-axis)", fontSize: 11 }}
              minTickGap={24}
              tickMargin={8}
            />
            <YAxis
              tickFormatter={formatAxisNumber}
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--viz-axis)", fontSize: 11 }}
              width={44}
              allowDecimals={false}
              domain={yMax === undefined ? undefined : [0, yMax]}
            />
            <Tooltip
              cursor={{ stroke: "var(--viz-axis)", strokeWidth: 1 }}
              isAnimationActive={false}
              content={(props) => {
                if (!props.active || props.label === undefined) return null;
                const point = pointsByDate.get(String(props.label));
                if (!point) return null;
                return <TimeSeriesTooltip point={point} series={series} />;
              }}
            />
            {series.map((spec) => (
              <Line
                key={spec.key}
                type="linear"
                dataKey={spec.key}
                name={spec.label}
                stroke={spec.color}
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
                connectNulls={false}
                isAnimationActive={false}
                activeDot={{
                  r: 4,
                  strokeWidth: 2,
                  stroke: "var(--viz-surface)",
                }}
                dot={(dotProps) => {
                  const { cx, cy, index } = dotProps;
                  if (cx === undefined || cy === undefined) return null;
                  if (!isolatedIndexes.get(spec.key)?.has(index)) return null;
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill={spec.color}
                      stroke="var(--viz-surface)"
                      strokeWidth={2}
                    />
                  );
                }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </>
  );
}

function TimeSeriesTooltip({
  point,
  series,
}: {
  point: PerformancePoint;
  series: SeriesSpec<string>[];
}) {
  return (
    <div className="min-w-44 rounded-lg border border-card-border bg-card-background px-3 py-2.5 shadow-lg">
      <p className="text-xs font-medium text-text-tertiary">{formatPointDate(point.date)}</p>
      <ul className="mt-2 flex flex-col gap-1.5">
        {series.map((spec) => {
          const value = metricValue(point, spec.key);
          return (
            <li key={spec.key} className="flex items-baseline gap-2">
              <span
                aria-hidden="true"
                className="h-0.5 w-3.5 shrink-0 translate-y-[-3px] rounded-full"
                style={{ backgroundColor: spec.color }}
              />
              <span className="text-sm font-semibold text-text-primary tabular-nums">
                {formatExact(value) ?? "Not reported"}
              </span>
              <span className="text-xs text-text-tertiary">{spec.label}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
