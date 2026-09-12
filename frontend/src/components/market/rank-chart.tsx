"use client";

import type { RankPoint } from "@/services/api/market";
import type { ReactNode } from "react";
import type { DotItemDotProps } from "recharts/types/util/types";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipContentProps } from "recharts/types/component/Tooltip";
import { formatWeek, formatWeekLong, isNotFound, NOT_FOUND_LABEL } from "./rank-format";

/*
 * Colours come from the data-viz palette, stepped separately for each surface and
 * validated against both of them. They are declared as custom properties rather than
 * Tailwind classes because Recharts needs real values on SVG attributes; the
 * `[data-theme="dark"]` scope is what the app's theme toggle actually sets.
 */
const CHART_CSS = `
.locus-rank-chart {
  --rank-line: #2a78d6;
  --rank-pack: #1baf7a;
  --rank-missing: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) .locus-rank-chart {
    --rank-line: #3987e5;
    --rank-pack: #199e70;
    --rank-missing: #d03b3b;
  }
}
[data-theme="dark"] .locus-rank-chart {
  --rank-line: #3987e5;
  --rank-pack: #199e70;
  --rank-missing: #d03b3b;
}
`;

interface RankDatum {
  weekStart: string;
  weekLabel: string;
  /** Null when the business was not found — the line breaks rather than dropping to zero. */
  rank: number | null;
  localPack: number | null;
  /** Set to the sentinel row value only for the weeks with no result at all. */
  notFound: number | null;
}

interface RankScale {
  data: RankDatum[];
  /** The y value of the dedicated "Not found" row below the plot. */
  notFoundValue: number;
  ticks: number[];
  /** Hairline between the plot and the "Not found" row. */
  divider: number;
}

/**
 * Builds the y scale from the data. Position 1 is the best result, so the axis is
 * reversed and "not found" gets its own labelled row below the worst position rather
 * than a zero or a silent gap.
 */
function buildRankScale(points: RankPoint[]): RankScale {
  const ranks = points
    .filter((point) => !isNotFound(point))
    .map((point) => point.rank_absolute as number);
  const worst = ranks.length > 0 ? Math.max(...ranks) : 10;
  const step = Math.max(2, Math.ceil(Math.max(worst, 10) / 5));
  const axisMax = Math.ceil(Math.max(worst, 10) / step) * step;
  const notFoundValue = axisMax + step;

  const ticks = [1];
  for (let value = step; value <= axisMax; value += step) {
    if (value > 1) ticks.push(value);
  }
  ticks.push(notFoundValue);

  return {
    data: points.map((point) => {
      const missing = isNotFound(point);
      return {
        weekStart: point.week_start,
        weekLabel: formatWeek(point.week_start),
        rank: missing ? null : point.rank_absolute,
        localPack: point.rank_in_local_pack,
        notFound: missing ? notFoundValue : null,
      };
    }),
    notFoundValue,
    ticks,
    divider: axisMax + step / 2,
  };
}

function toNumber(value: number | string | undefined) {
  return typeof value === "number" ? value : Number(value ?? Number.NaN);
}

/**
 * Weeks inside the three-result local pack get a larger ringed marker, so the
 * commercially important outcome is distinguishable by size as well as by hue.
 */
function renderRankDot(props: DotItemDotProps) {
  const { cx, cy, payload, index } = props;
  const datum = payload as RankDatum;
  const x = toNumber(cx);
  const y = toNumber(cy);
  if (datum?.rank === null || Number.isNaN(x) || Number.isNaN(y)) return null;

  const inLocalPack = datum.localPack !== null;

  return (
    <circle
      key={`rank-${index}`}
      cx={x}
      cy={y}
      r={inLocalPack ? 5 : 4}
      fill={inLocalPack ? "var(--rank-pack)" : "var(--rank-line)"}
      stroke="var(--card-background)"
      strokeWidth={2}
    />
  );
}

/** A cross on the "Not found" row — an outcome with its own mark, never a gap. */
function renderNotFoundDot(props: DotItemDotProps) {
  const { cx, cy, payload, index } = props;
  const datum = payload as RankDatum;
  const x = toNumber(cx);
  const y = toNumber(cy);
  if (datum?.notFound === null || Number.isNaN(x) || Number.isNaN(y)) return null;

  const arm = 4.5;

  return (
    <g key={`missing-${index}`} stroke="var(--rank-missing)" strokeWidth={2} strokeLinecap="round">
      <line x1={x - arm} y1={y - arm} x2={x + arm} y2={y + arm} />
      <line x1={x - arm} y1={y + arm} x2={x + arm} y2={y - arm} />
    </g>
  );
}

function RankTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload?.length) return null;
  const datum = payload[0]?.payload as RankDatum | undefined;
  if (!datum) return null;

  return (
    <div className="rounded-lg border border-card-border bg-card-background px-3 py-2 text-xs leading-5 shadow-md">
      <p className="font-semibold text-text-primary">Week of {formatWeekLong(datum.weekStart)}</p>
      <p className="mt-0.5 text-text-secondary tabular-nums">
        {datum.rank === null ? NOT_FOUND_LABEL : `Position #${datum.rank}`}
      </p>
      <p className="text-text-tertiary">
        {datum.localPack === null
          ? "Outside the local pack"
          : `Local pack #${datum.localPack}`}
      </p>
    </div>
  );
}

function LegendKey({
  children,
  swatch,
}: {
  children: ReactNode;
  swatch: ReactNode;
}) {
  return (
    <span className="inline-flex items-center gap-2 text-xs leading-4 text-text-secondary">
      {swatch}
      {children}
    </span>
  );
}

export interface RankChartProps {
  points: RankPoint[];
  /** Names the single measure plotted, so the chart needs no title-restating legend. */
  keyword: string;
}

export function RankChart({ points, keyword }: RankChartProps) {
  const scale = buildRankScale(points);

  return (
    <div className="locus-rank-chart">
      <style>{CHART_CSS}</style>

      <p className="text-xs leading-5 text-text-tertiary">
        Weekly position for “{keyword}”. Position 1 is the best result, so the axis runs
        with 1 at the top — a line moving up is improving.
      </p>

      <div className="mt-4 h-72 w-full sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={scale.data}
            margin={{ top: 8, right: 12, bottom: 4, left: 0 }}
            accessibilityLayer
          >
            <CartesianGrid vertical={false} stroke="var(--card-border)" />
            <XAxis
              dataKey="weekLabel"
              tickLine={false}
              axisLine={{ stroke: "var(--card-border)" }}
              tick={{ fill: "var(--text-tertiary)", fontSize: 11 }}
              minTickGap={16}
            />
            <YAxis
              reversed
              type="number"
              domain={[1, scale.notFoundValue]}
              ticks={scale.ticks}
              width={78}
              tickLine={false}
              axisLine={false}
              tick={{ fill: "var(--text-tertiary)", fontSize: 11 }}
              tickFormatter={(value: number) =>
                value === scale.notFoundValue ? NOT_FOUND_LABEL : `#${value}`
              }
            />
            <ReferenceLine y={scale.divider} stroke="var(--card-border)" />
            <Tooltip
              content={RankTooltip}
              cursor={{ stroke: "var(--card-border)", strokeWidth: 1 }}
              wrapperStyle={{ outline: "none" }}
            />
            <Line
              type="linear"
              dataKey="rank"
              name="Position"
              stroke="var(--rank-line)"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
              connectNulls={false}
              dot={renderRankDot}
              activeDot={{ r: 6, strokeWidth: 2, stroke: "var(--card-background)" }}
              isAnimationActive={false}
            />
            <Line
              type="linear"
              dataKey="notFound"
              name={NOT_FOUND_LABEL}
              stroke="none"
              connectNulls={false}
              dot={renderNotFoundDot}
              activeDot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2">
        <LegendKey
          swatch={
            <svg aria-hidden="true" focusable="false" width="22" height="10" viewBox="0 0 22 10">
              <line
                x1="1"
                y1="5"
                x2="21"
                y2="5"
                stroke="var(--rank-line)"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <circle cx="11" cy="5" r="4" fill="var(--rank-line)" />
            </svg>
          }
        >
          Position in results
        </LegendKey>
        <LegendKey
          swatch={
            <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 14 14">
              <circle cx="7" cy="7" r="5" fill="var(--rank-pack)" />
            </svg>
          }
        >
          In the local pack (larger dot)
        </LegendKey>
        <LegendKey
          swatch={
            <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 14 14">
              <g stroke="var(--rank-missing)" strokeWidth="2" strokeLinecap="round">
                <line x1="3" y1="3" x2="11" y2="11" />
                <line x1="3" y1="11" x2="11" y2="3" />
              </g>
            </svg>
          }
        >
          {NOT_FOUND_LABEL} that week
        </LegendKey>
      </div>
    </div>
  );
}
