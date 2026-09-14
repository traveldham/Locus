"use client";

import { SectionCard } from "@/components/common/section-card";
import type { Recommendation } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import { TONE_FILL, TONE_STROKE, TONE_TEXT } from "../audit-format";
import type { CategoryCardProps } from "./registry";

/** One metric over the current window against the window before. */
interface MetricDelta {
  current: number | null;
  previous: number | null;
  /** Relative change; null when either side is unknown or the previous is zero. */
  change: number | null;
  days: number;
  previous_days: number;
}

/** What the performance worker's `card(snapshot)` returns. */
export interface PerformanceCardData {
  window: {
    days: number;
    current_start: string;
    current_end: string;
    previous_start: string;
    previous_end: string;
    latest_date: string;
    data_age_days: number | null;
  } | null;
  days_with_data: number;
  metrics: Partial<
    Record<
      | "impressions"
      | "impressions_maps"
      | "impressions_search"
      | "calls"
      | "directions"
      | "website_clicks"
      | "conversations"
      | "bookings"
      | "action_rate",
      MetricDelta
    >
  >;
  maps_share: number | null;
  mobile_share: number | null;
  weekly_impressions: {
    start: string;
    end: string;
    impressions: number | null;
    days: number;
  }[];
}

const TILES: {
  key: keyof PerformanceCardData["metrics"];
  label: string;
  rate?: boolean;
}[] = [
  { key: "impressions", label: "Impressions" },
  { key: "calls", label: "Call button taps" },
  { key: "directions", label: "Direction requests" },
  { key: "website_clicks", label: "Website clicks" },
  { key: "action_rate", label: "Actions per impression", rate: true },
];

/** Which tile each check paints. */
const RULE_TILE: Record<string, keyof PerformanceCardData["metrics"]> = {
  impressions_decline: "impressions",
  calls_decline: "calls",
  directions_decline: "directions",
  website_clicks_decline: "website_clicks",
  action_rate_decline: "action_rate",
  zero_action_days: "action_rate",
};

const number = new Intl.NumberFormat("en-US");

function count(value: number | null, rate = false): string {
  if (value === null) return "—";
  return rate ? `${(value * 100).toFixed(1)}%` : number.format(value);
}

function shortDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function changeTone(change: number | null): "success" | "error" | "muted" {
  if (change === null || Math.abs(change) < 0.005) return "muted";
  return change < 0 ? "error" : "success";
}

function Tile({
  label,
  metric,
  rate,
  flagged,
}: {
  label: string;
  metric: MetricDelta | undefined;
  rate?: boolean;
  flagged: boolean;
}) {
  const change = metric?.change ?? null;
  const tone = changeTone(change);
  return (
    <div
      className={cn(
        "min-w-0 border-b px-1 py-4",
        flagged
          ? "border-badge-error-text/40 bg-badge-error-background"
          : "border-card-border",
      )}
    >
      <p className="text-sm text-text-secondary">{label}</p>
      <p className="mt-1 text-lg font-semibold tabular-nums text-text-primary">
        {count(metric?.current ?? null, rate)}
      </p>
      <p className="mt-0.5 text-xs tabular-nums text-text-secondary">
        {change === null ? (
          <span className="text-text-secondary">Change unavailable</span>
        ) : (
          <>
            <span className={cn("font-medium", TONE_TEXT[tone])}>
              {change > 0 ? "+" : ""}
              {(change * 100).toFixed(0)}%
            </span>{" "}
            <span className="text-text-tertiary">
              vs {count(metric?.previous ?? null, rate)}
            </span>
          </>
        )}
      </p>
      <p className="mt-1 text-xs text-text-secondary">
        Previous: {count(metric?.previous ?? null, rate)}
      </p>
      {metric ? (
        <p className="mt-2 text-xs text-text-tertiary">
          {metric.days} current / {metric.previous_days} previous days reported
        </p>
      ) : null}
      {flagged ? (
        <p className="mt-2 text-xs font-medium text-badge-error-text">
          Needs attention
        </p>
      ) : null}
    </div>
  );
}

/** Twelve weekly impression totals. A week with no data leaves a gap in the line. */
function WeeklySparkline({
  weeks,
}: {
  weeks: PerformanceCardData["weekly_impressions"];
}) {
  const known = weeks.filter((w) => w.impressions !== null);
  if (known.length < 2) {
    return (
      <p className="text-xs leading-5 text-text-tertiary">
        Not enough weeks with data to draw a trend.
      </p>
    );
  }
  const width = 320;
  const height = 64;
  const pad = 6;
  const max = Math.max(...known.map((w) => w.impressions as number), 1);
  const x = (i: number) => pad + (i * (width - 2 * pad)) / (weeks.length - 1);
  const y = (v: number) => height - pad - (v / max) * (height - 2 * pad);
  let path = "";
  let pen = false;
  weeks.forEach((w, i) => {
    if (w.impressions === null) {
      pen = false;
      return;
    }
    path += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(w.impressions).toFixed(1)} `;
    pen = true;
  });
  const first = known[0].impressions as number;
  const last = known[known.length - 1].impressions as number;
  const tone = changeTone(first > 0 ? (last - first) / first : null);
  return (
    <div>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Weekly impressions over ${weeks.length} weeks, from ${number.format(first)} to ${number.format(last)}`}
        className="h-auto max-w-full"
      >
        <path
          d={path.trim()}
          fill="none"
          strokeWidth={2}
          strokeLinejoin="round"
          className={cn(TONE_STROKE[tone === "muted" ? "muted" : tone])}
        />
        {weeks.map((w, i) =>
          w.impressions === null ? null : (
            <circle
              key={w.start}
              cx={x(i)}
              cy={y(w.impressions)}
              r={w.days < 7 ? 2 : 3}
              className={cn(
                "fill-current",
                w.days < 7 ? TONE_TEXT.muted : TONE_TEXT[tone],
              )}
            >
              <title>
                {`${shortDate(w.start)} to ${shortDate(w.end)}: ${number.format(w.impressions)} impressions over ${w.days} days`}
              </title>
            </circle>
          ),
        )}
      </svg>
      <p className="mt-1 text-xs leading-5 text-text-tertiary">
        {shortDate(weeks[0].start)} to {shortDate(weeks[weeks.length - 1].end)}{" "}
        · {number.format(last)} last week. Smaller points are weeks with missing
        days.
      </p>
    </div>
  );
}

function SplitBar({
  label,
  share,
  left,
  right,
}: {
  label: string;
  share: number | null;
  left: string;
  right: string;
}) {
  if (share === null) {
    return <p className="text-xs text-text-tertiary">{label}: no comparison</p>;
  }
  const pct = Math.round(share * 100);
  return (
    <div>
      <div className="flex items-center justify-between text-xs text-text-secondary">
        <span>
          {left}{" "}
          <span className="font-medium tabular-nums text-text-primary">
            {pct}%
          </span>
        </span>
        <span>
          {right}{" "}
          <span className="font-medium tabular-nums text-text-primary">
            {100 - pct}%
          </span>
        </span>
      </div>
      <div
        className="mt-1 flex h-2 overflow-hidden rounded-full bg-background-gray-secondary"
        role="img"
        aria-label={`${label}: ${left} ${pct}%, ${right} ${100 - pct}%`}
      >
        <div
          className={cn("h-full", TONE_FILL.success)}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function InvestigationPlans({ items }: { items: Recommendation[] }) {
  const planned = items.filter(
    (i) =>
      i.suggestion?.field === "investigation_plan" &&
      Array.isArray(i.suggestion.value),
  );
  if (!planned.length) return null;
  return (
    <div className="space-y-4">
      {planned.map((item) => (
        <section
          key={item.key}
          aria-label={`Investigation plan: ${item.title}`}
          className="rounded-lg bg-background-gray-secondary px-4 py-3"
        >
          <p className="text-sm font-medium text-text-primary">
            {item.title}
            <span className="ml-2 text-xs font-normal text-text-tertiary">
              drafted plan · {item.suggestion?.confidence} confidence
            </span>
          </p>
          <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm leading-6 text-text-secondary">
            {(item.suggestion?.value as string[]).map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          {item.suggestion?.reason ? (
            <p className="mt-2 text-xs leading-5 text-text-tertiary">
              {item.suggestion.reason}
            </p>
          ) : null}
        </section>
      ))}
    </div>
  );
}

/** Four weeks of impressions and actions against the four weeks before. */
export function PerformanceCard({ card, items }: CategoryCardProps) {
  const data = card as PerformanceCardData;
  if (!data?.window) {
    return (
      <p className="rounded-xl border border-card-border bg-card-background px-5 py-6 text-sm text-text-secondary">
        No performance data is stored for this profile yet.
      </p>
    );
  }
  const flagged = new Set(
    items.map((i) => RULE_TILE[i.rule]).filter((tile) => tile !== undefined),
  );
  const { window } = data;
  const age = window.data_age_days;
  return (
    <SectionCard
      title="Impressions and actions"
      bodyClassName="px-5 py-5"
      actions={
        <span className="text-xs text-text-tertiary">
          {shortDate(window.current_start)} to {shortDate(window.current_end)}{" "}
          vs the {window.days} days before
        </span>
      }
    >
      <div className="space-y-6">
        <div className="grid gap-3 border-b border-card-border pb-5 sm:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold text-text-primary">
              How people find and use your profile
            </h3>
            <p className="mt-1 max-w-prose text-sm leading-6 text-text-secondary">
              Impressions count profile views. Calls, directions and website
              clicks show the actions taken from those views.
            </p>
          </div>
          <dl className="space-y-1 text-sm">
            <div className="flex flex-wrap justify-between gap-x-3">
              <dt className="text-text-secondary">Current period</dt>
              <dd className="font-medium text-text-primary">
                {shortDate(window.current_start)} –{" "}
                {shortDate(window.current_end)}
              </dd>
            </div>
            <div className="flex flex-wrap justify-between gap-x-3">
              <dt className="text-text-secondary">Previous period</dt>
              <dd className="font-medium text-text-primary">
                {shortDate(window.previous_start)} –{" "}
                {shortDate(window.previous_end)}
              </dd>
            </div>
          </dl>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {TILES.map((tile) => (
            <Tile
              key={tile.key}
              label={tile.label}
              metric={data.metrics[tile.key]}
              rate={tile.rate}
              flagged={flagged.has(tile.key)}
            />
          ))}
        </div>

        <details className="border-b border-card-border pb-2">
          <summary className="flex min-h-11 cursor-pointer items-center text-sm text-primary-500 focus-visible:outline-2 focus-visible:outline-primary-500">
            More reported metrics: Maps, Search, messages and bookings
          </summary>
          <div className="grid grid-cols-2 gap-3 pb-3 lg:grid-cols-4">
            <Tile
              label="Maps impressions"
              metric={data.metrics.impressions_maps}
              flagged={false}
            />
            <Tile
              label="Search impressions"
              metric={data.metrics.impressions_search}
              flagged={false}
            />
            <Tile
              label="Conversations started"
              metric={data.metrics.conversations}
              flagged={false}
            />
            <Tile
              label="Profile-attributed bookings"
              metric={data.metrics.bookings}
              flagged={false}
            />
          </div>
          <p className="pb-3 text-xs leading-5 text-text-secondary">
            These are reported profile metrics. Profile-attributed bookings can
            differ from the appointment requests shown in Operations.
          </p>
        </details>

        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div className="min-w-0">
            <p className="mb-2 text-sm font-semibold text-text-primary">
              Weekly impressions
            </p>
            <WeeklySparkline weeks={data.weekly_impressions} />
            <details className="mt-3 text-sm">
              <summary className="flex min-h-11 cursor-pointer items-center text-primary-500 focus-visible:outline-2 focus-visible:outline-primary-500">
                View weekly totals
              </summary>
              <ul className="divide-y divide-card-border">
                {data.weekly_impressions.map((week) => (
                  <li
                    key={week.start}
                    className="flex flex-wrap justify-between gap-2 py-2 text-text-secondary"
                  >
                    <span>
                      {shortDate(week.start)} – {shortDate(week.end)}
                    </span>
                    <span className="tabular-nums">
                      {count(week.impressions)} · {week.days} days reported
                    </span>
                  </li>
                ))}
              </ul>
            </details>
          </div>
          <div className="min-w-0 space-y-4">
            <SplitBar
              label="Surface"
              share={data.maps_share}
              left="Maps"
              right="Search"
            />
            <SplitBar
              label="Device"
              share={data.mobile_share}
              left="Mobile"
              right="Desktop"
            />
          </div>
        </div>

        <p className="text-xs leading-5 text-text-tertiary">
          {data.days_with_data} of {window.days} days have data
          {age !== null && age > 0
            ? `; the newest day is ${shortDate(window.latest_date)}, ${age} day${age === 1 ? "" : "s"} before the audit date`
            : ""}
          . Missing days and unreported metrics are left out, never counted as
          zero. The action rate uses calls, directions and website clicks per
          impression; it does not measure unique customers or completed
          appointments. Unequal reporting coverage can affect comparisons.
        </p>

        <InvestigationPlans items={items} />
      </div>
    </SectionCard>
  );
}
