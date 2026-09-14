"use client";

import { SectionCard } from "@/components/common/section-card";
import type { Recommendation } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import { TONE_STROKE, TONE_TEXT, scoreTone } from "../audit-format";
import type { CategoryCardProps } from "./registry";

/** What the visibility worker's `card(snapshot)` returns. */
export interface VisibilityCardData {
  latest_week: string | null;
  weeks: string[];
  keywords_tracked: number;
  in_pack: number;
  near_pack: number;
  not_found: number;
  pack_share: number | null;
  best: { keyword: string; position: number } | null;
  worst: { keyword: string; position: number } | null;
  keywords: {
    keyword: string;
    intent: string | null;
    device: string | null;
    position: number | null;
    in_pack: boolean;
    trend: (number | null)[];
    weeks_in_pack: number;
  }[];
  top_terms: {
    term: string;
    impressions: number | null;
    is_threshold: boolean;
    change: number | null;
  }[];
  terms_month: string | null;
  rivals_ahead: {
    name: string;
    keywords_ahead: number;
    review_count: number | null;
    average_rating: number | null;
    photo_count: number | null;
  }[];
  ours: {
    review_count: number | null;
    average_rating: number | null;
    photo_count: number | null;
  };
}

const KEYWORD_RULES = new Set([
  "pack_lost",
  "near_pack_opportunity",
  "not_found_persistent",
  "rank_dropped",
  "high_intent_lagging",
  "branded_not_first",
]);

const RULE_TAG: Record<string, string> = {
  pack_lost: "left the pack",
  near_pack_opportunity: "within reach",
  not_found_persistent: "never found",
  rank_dropped: "fell",
  high_intent_lagging: "lagging",
  branded_not_first: "brand not first",
};

function isVisibilityCard(card: unknown): card is VisibilityCardData {
  return (
    typeof card === "object" &&
    card !== null &&
    Array.isArray((card as VisibilityCardData).keywords) &&
    Array.isArray((card as VisibilityCardData).top_terms)
  );
}

function draftFor(item: Recommendation | undefined): string | null {
  const s = item?.suggestion;
  if (!s) return null;
  if (typeof s.value === "string") return s.value;
  if (!Array.isArray(s.value) && typeof s.value === "object") {
    const first = Object.values(s.value)[0];
    return typeof first === "string" ? first : null;
  }
  return null;
}

function formatChange(change: number | null): string {
  if (change === null) return "no comparison";
  const pct = Math.round(change * 100);
  return `${pct > 0 ? "+" : ""}${pct}%`;
}

function ordinal(position: number | null): string {
  return position === null ? "—" : `#${position}`;
}

/** A ring showing the share of tracked keywords inside the local pack. */
function PackRing({
  share,
  inPack,
  tracked,
}: {
  share: number | null;
  inPack: number;
  tracked: number;
}) {
  const radius = 34;
  const circumference = 2 * Math.PI * radius;
  const value = share ?? 0;
  const tone =
    share === null
      ? "muted"
      : scoreTone(Math.round(share * 100) >= 25 ? 75 : 25);
  return (
    <div className="flex items-center gap-4">
      <svg
        viewBox="0 0 80 80"
        className="size-20 shrink-0"
        role="img"
        aria-label={`${inPack} of ${tracked} keywords in the local pack`}
      >
        <circle
          cx="40"
          cy="40"
          r={radius}
          fill="none"
          strokeWidth="8"
          className="stroke-background-gray-secondary"
        />
        <circle
          cx="40"
          cy="40"
          r={radius}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${circumference * value} ${circumference}`}
          transform="rotate(-90 40 40)"
          className={TONE_STROKE[tone]}
        />
        <text
          x="40"
          y="45"
          textAnchor="middle"
          className="fill-text-primary text-[16px] font-semibold"
        >
          {share === null ? "—" : `${Math.round(share * 100)}%`}
        </text>
      </svg>
      <div>
        <p className="text-sm font-medium text-text-primary">
          Local pack share
        </p>
        <p className="mt-0.5 text-xs leading-5 text-text-secondary">
          {inPack} of {tracked} tracked keywords put the profile in
          Google&apos;s three-result pack in the latest week.
        </p>
      </div>
    </div>
  );
}

/** Four weekly positions as a tiny line; lower is better so the axis is flipped. */
function Sparkline({ trend }: { trend: (number | null)[] }) {
  const points = trend.map((p, i) => ({
    x: 4 + i * 14,
    y: p === null ? null : 4 + Math.min(20, p),
  }));
  const path = points
    .map((p, index) =>
      p.y === null
        ? ""
        : `${index > 0 && points[index - 1].y !== null ? "L" : "M"}${p.x} ${p.y}`,
    )
    .join(" ");
  return (
    <svg
      viewBox="0 0 50 28"
      className="h-7 w-12"
      role="img"
      aria-label={`Weekly positions, oldest first: ${trend.map((position) => (position === null ? "not available" : position)).join(", ")}. Lower positions are better.`}
    >
      <line
        x1="4"
        x2="46"
        y1="7"
        y2="7"
        className="stroke-badge-success-text/40"
        strokeDasharray="2 2"
      />
      <path
        d={path}
        fill="none"
        strokeWidth="1.5"
        className="stroke-text-secondary"
      />
      {points.map((p, i) =>
        p.y === null ? (
          <text
            key={i}
            x={p.x}
            y="24"
            textAnchor="middle"
            className="fill-badge-error-text text-[8px]"
          >
            ×
          </text>
        ) : (
          <circle
            key={i}
            cx={p.x}
            cy={p.y}
            r="1.8"
            className={
              p.y <= 7 ? "fill-badge-success-text" : "fill-text-secondary"
            }
          />
        ),
      )}
    </svg>
  );
}

function Counter({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: keyof typeof TONE_TEXT;
}) {
  return (
    <div className="border-b border-card-border px-1 py-3">
      <p className={cn("text-2xl font-semibold tabular-nums", TONE_TEXT[tone])}>
        {value}
      </p>
      <p className="text-xs text-text-secondary">{label}</p>
    </div>
  );
}

/** The tracker's view: pack share, the keyword table, search terms and rivals. */
export function VisibilityCard({ card, items }: CategoryCardProps) {
  if (!isVisibilityCard(card)) return null;
  const byKeyword = new Map<string, Recommendation[]>();
  for (const item of items) {
    if (!KEYWORD_RULES.has(item.rule) || !item.subject) continue;
    byKeyword.set(item.subject, [...(byKeyword.get(item.subject) ?? []), item]);
  }
  const byTerm = new Map(
    items
      .filter((i) => i.rule === "search_term_losing")
      .map((i) => [i.subject, i] as const),
  );
  const rivalsFlagged = new Set(
    items.filter((i) => i.rule === "rival_ahead_gap").map((i) => i.subject),
  );
  const stale = items.some((i) => i.rule === "tracking_stale");

  return (
    <SectionCard
      title="Where the profile shows up"
      bodyClassName="px-5 py-5"
      actions={
        <span className="text-xs text-text-tertiary">
          {card.latest_week
            ? `Rank checks to the week of ${card.latest_week}`
            : "No rank checks"}
          {card.terms_month ? ` · search terms for ${card.terms_month}` : ""}
        </span>
      }
    >
      <p className="mb-5 max-w-prose text-sm leading-6 text-text-secondary">
        See how often this profile appears in Google’s three local results for
        the keywords you track. Positions are recorded checks for a particular
        keyword and device, not a prediction for every searcher.
      </p>
      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <PackRing
          share={card.pack_share}
          inPack={card.in_pack}
          tracked={card.keywords_tracked}
        />
        <div className="grid grid-cols-3 gap-2">
          <Counter label="in the pack" value={card.in_pack} tone="success" />
          <Counter label="within reach" value={card.near_pack} tone="warning" />
          <Counter
            label="not found"
            value={card.not_found}
            tone={card.not_found ? "error" : "muted"}
          />
        </div>
      </div>
      {stale ? (
        <p className="mt-4 rounded-lg border border-badge-warning-text/40 bg-badge-warning-background px-3 py-2 text-sm text-badge-warning-text">
          Rank tracking is stale, so the keyword positions below are older than
          the freshness window.
        </p>
      ) : null}
      {card.best || card.worst ? (
        <p className="mt-4 text-sm text-text-secondary">
          {card.best ? (
            <>
              Best:{" "}
              <span className="text-text-primary">“{card.best.keyword}”</span>{" "}
              at {ordinal(card.best.position)}.
            </>
          ) : null}{" "}
          {card.worst && card.worst.keyword !== card.best?.keyword ? (
            <>
              Weakest found:{" "}
              <span className="text-text-primary">“{card.worst.keyword}”</span>{" "}
              at {ordinal(card.worst.position)}.
            </>
          ) : null}
        </p>
      ) : null}

      <p className="mt-5 text-xs leading-5 text-text-secondary">
        Lower position numbers are better. The four-week trend runs oldest to
        newest; gaps mean no position is available. Scroll the table
        horizontally on smaller screens.
      </p>
      <div
        className="mt-2 overflow-x-auto"
        role="region"
        aria-label="Keyword positions"
        tabIndex={0}
      >
        <table className="w-full min-w-[520px] text-sm">
          <caption className="sr-only">
            Tracked keywords with latest position and four-week trend
          </caption>
          <thead>
            <tr className="border-b border-card-border text-left text-xs text-text-tertiary">
              <th scope="col" className="py-2 pr-3 font-medium">
                Keyword
              </th>
              <th scope="col" className="py-2 pr-3 font-medium">
                Intent
              </th>
              <th scope="col" className="py-2 pr-3 text-right font-medium">
                Position
              </th>
              <th scope="col" className="py-2 pr-3 font-medium">
                4 weeks
              </th>
              <th scope="col" className="py-2 font-medium">
                Status and draft
              </th>
            </tr>
          </thead>
          <tbody>
            {card.keywords.map((k) => {
              const flags = byKeyword.get(k.keyword) ?? [];
              const draft = draftFor(flags.find((f) => f.suggestion));
              return (
                <tr
                  key={k.keyword}
                  className="border-b border-card-border align-top last:border-b-0"
                >
                  <td className="py-2.5 pr-3 text-text-primary">
                    {k.keyword}
                    {k.device ? (
                      <span className="ml-1 text-xs text-text-tertiary">
                        {k.device}
                      </span>
                    ) : null}
                  </td>
                  <td className="py-2.5 pr-3 text-text-secondary">
                    {k.intent ?? "—"}
                  </td>
                  <td
                    className={cn(
                      "py-2.5 pr-3 text-right tabular-nums",
                      k.in_pack
                        ? "font-semibold text-badge-success-text"
                        : k.position === null
                          ? "text-badge-error-text"
                          : "text-text-primary",
                    )}
                  >
                    {ordinal(k.position)}
                  </td>
                  <td className="py-2.5 pr-3">
                    <Sparkline trend={k.trend} />
                  </td>
                  <td className="py-2.5">
                    {flags.length ? (
                      <div className="flex flex-wrap gap-1">
                        {flags.map((f) => (
                          <span
                            key={f.key}
                            className={cn(
                              "rounded-full px-2 py-0.5 text-xs",
                              f.severity === "critical"
                                ? "bg-badge-error-background text-badge-error-text"
                                : f.severity === "warning"
                                  ? "bg-badge-warning-background text-badge-warning-text"
                                  : "bg-background-gray-secondary text-text-secondary",
                            )}
                          >
                            {RULE_TAG[f.rule] ?? f.rule}
                          </span>
                        ))}
                      </div>
                    ) : k.in_pack ? (
                      <span className="text-xs text-badge-success-text">
                        in the pack
                      </span>
                    ) : (
                      <span className="text-xs text-text-tertiary">—</span>
                    )}
                    {draft ? (
                      <p className="mt-1 text-xs leading-5 text-text-secondary">
                        <span className="font-medium text-primary-500">
                          Draft:
                        </span>{" "}
                        {draft}
                      </p>
                    ) : null}
                  </td>
                </tr>
              );
            })}
            {!card.keywords.length ? (
              <tr>
                <td
                  colSpan={5}
                  className="py-6 text-center text-sm text-text-secondary"
                >
                  No keywords are tracked for this profile.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-text-primary">
            Top search terms{card.terms_month ? ` · ${card.terms_month}` : ""}
          </h3>
          <p className="mt-1 text-xs leading-5 text-text-secondary">
            Impressions with change from the previous month. Google may omit
            low-volume terms, so these counts do not equal total profile views.
          </p>
          {card.top_terms.length ? (
            <ul className="mt-2 space-y-2">
              {card.top_terms.map((t) => {
                const flagged = byTerm.get(t.term);
                const draft = draftFor(flagged);
                return (
                  <li key={t.term} className="text-sm">
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="min-w-0 break-words text-text-primary">
                        {t.term}
                      </span>
                      <span className="shrink-0 tabular-nums text-text-secondary">
                        {t.is_threshold ? "under " : ""}
                        {t.impressions ?? "—"}
                        <span
                          className={cn(
                            "ml-2 text-xs",
                            t.change === null
                              ? "text-text-tertiary"
                              : t.change < 0
                                ? "text-badge-error-text"
                                : "text-badge-success-text",
                          )}
                        >
                          {formatChange(t.change)}
                        </span>
                      </span>
                    </div>
                    {flagged ? (
                      <p className="mt-0.5 text-xs leading-5 text-text-secondary">
                        <span className="text-badge-warning-text">
                          Losing impressions.
                        </span>
                        {draft ? (
                          <>
                            {" "}
                            <span className="font-medium text-primary-500">
                              Draft:
                            </span>{" "}
                            {draft}
                          </>
                        ) : null}
                      </p>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-text-secondary">
              No search terms stored.
            </p>
          )}
        </div>
        <div>
          <h3 className="text-sm font-semibold text-text-primary">
            Rivals ahead this week
          </h3>
          {card.rivals_ahead.length ? (
            <ul className="mt-2 space-y-2">
              {card.rivals_ahead.map((r) => (
                <li key={r.name} className="text-sm">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="min-w-0 truncate text-text-primary">
                      {r.name}
                      {rivalsFlagged.has(r.name) ? (
                        <span className="ml-2 rounded-full bg-badge-warning-background px-2 py-0.5 text-xs text-badge-warning-text">
                          stronger profile
                        </span>
                      ) : null}
                    </span>
                    <span className="shrink-0 text-xs text-text-secondary">
                      ahead on {r.keywords_ahead}{" "}
                      {r.keywords_ahead === 1 ? "keyword" : "keywords"}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-text-tertiary">
                    {r.review_count ?? "—"} reviews ·{" "}
                    {r.average_rating?.toFixed(1) ?? "—"} rating ·{" "}
                    {r.photo_count ?? "—"} photos
                  </p>
                </li>
              ))}
              <li className="border-t border-card-border pt-2 text-xs text-text-tertiary">
                You: {card.ours.review_count ?? "—"} reviews ·{" "}
                {card.ours.average_rating?.toFixed(1) ?? "—"} rating ·{" "}
                {card.ours.photo_count ?? "—"} photos
              </li>
            </ul>
          ) : (
            <p className="mt-2 text-sm text-text-secondary">
              No rival is ranked ahead in the latest week.
            </p>
          )}
        </div>
      </div>
    </SectionCard>
  );
}
