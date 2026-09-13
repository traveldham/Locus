"use client";

import { SectionCard } from "@/components/common/section-card";
import type { Recommendation } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import { TONE_FILL, TONE_STROKE, TONE_TEXT } from "../audit-format";
import type { CategoryCardProps } from "./registry";

/** What the reputation worker's `card(snapshot)` returns. */
export interface ReputationCardData {
  average: number | null;
  count: number;
  rated_count: number;
  distribution: Record<"5" | "4" | "3" | "2" | "1", number>;
  replied_share: number | null;
  median_reply_days: number | null;
  last_review_date: string | null;
  unanswered_critical_count: number;
  unanswered: {
    id: string;
    rating: number | null;
    date: string;
    comment: string;
  }[];
}

const STARS = ["5", "4", "3", "2", "1"] as const;

function ratingTone(average: number | null) {
  if (average === null) return "muted" as const;
  if (average >= 4.5) return "success" as const;
  if (average >= 4) return "warning" as const;
  return "error" as const;
}

function shareTone(share: number | null, good: number, fair: number) {
  if (share === null) return "muted" as const;
  if (share >= good) return "success" as const;
  if (share >= fair) return "warning" as const;
  return "error" as const;
}

function daysTone(days: number | null, good: number, fair: number) {
  if (days === null) return "muted" as const;
  if (days <= good) return "success" as const;
  if (days <= fair) return "warning" as const;
  return "error" as const;
}

function daysAgo(iso: string | null): number | null {
  if (!iso) return null;
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return null;
  return Math.max(0, Math.floor((Date.now() - then) / 86_400_000));
}

function RatingRing({
  average,
  size = 96,
}: {
  average: number | null;
  size?: number;
}) {
  const tone = ratingTone(average);
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const filled = average === null ? 0 : (average / 5) * circumference;
  return (
    <span
      className="relative inline-flex shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={
        average === null
          ? "No rating yet"
          : `${average.toFixed(1)} out of 5 stars`
      }
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        aria-hidden="true"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          className="stroke-card-border"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className={cn(
            "transition-[stroke-dasharray] duration-500",
            TONE_STROKE[tone],
          )}
        />
      </svg>
      <span className="absolute inset-0 flex flex-col items-center justify-center">
        <span
          className={cn(
            "text-2xl font-semibold tracking-[-0.02em]",
            TONE_TEXT[tone],
          )}
        >
          {average === null ? "—" : average.toFixed(1)}
        </span>
        <span className="text-[10px] text-text-tertiary">of 5</span>
      </span>
    </span>
  );
}

function Stat({
  label,
  value,
  tone,
  hint,
}: {
  label: string;
  value: string;
  tone: keyof typeof TONE_TEXT;
  hint?: string;
}) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-text-tertiary">{label}</dt>
      <dd
        className={cn(
          "mt-0.5 text-lg font-semibold tracking-[-0.01em]",
          TONE_TEXT[tone],
        )}
      >
        {value}
      </dd>
      {hint ? (
        <dd className="text-xs leading-5 text-text-secondary">{hint}</dd>
      ) : null}
    </div>
  );
}

/** Reviews as a customer sees them, and the low reviews still waiting for a reply. */
export function ReputationCard({ card: raw, items }: CategoryCardProps) {
  const card = raw as ReputationCardData;
  const drafts = new Map<string, Recommendation>();
  for (const item of items) {
    if (item.rule === "critical_review_unanswered" && item.subject)
      drafts.set(item.subject, item);
  }
  const maxBar = Math.max(1, ...STARS.map((s) => card.distribution[s] ?? 0));
  const lastAge = daysAgo(card.last_review_date);
  const replyPct =
    card.replied_share === null ? null : Math.round(card.replied_share * 100);

  return (
    <SectionCard
      title="What customers see"
      bodyClassName="px-5 py-5"
      actions={
        <span className="text-xs text-text-tertiary">
          {card.count} {card.count === 1 ? "review" : "reviews"} stored
        </span>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[auto_1fr]">
        <div className="flex items-center gap-5">
          <RatingRing average={card.average} />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-text-primary">
              {card.rated_count} rated{" "}
              {card.rated_count === 1 ? "review" : "reviews"}
            </p>
            <p className="mt-0.5 text-xs leading-5 text-text-secondary">
              {card.average === null
                ? "Not enough ratings to average."
                : card.average >= 4
                  ? "Above the 4-star line most customers filter at."
                  : "Below the 4-star line most customers filter at."}
            </p>
            <ul className="mt-3 space-y-1" aria-label="Ratings by star">
              {STARS.map((star) => {
                const n = card.distribution[star] ?? 0;
                const share = card.rated_count ? n / card.rated_count : 0;
                return (
                  <li
                    key={star}
                    className="flex items-center gap-2 text-xs text-text-secondary"
                  >
                    <span className="w-3 text-right tabular-nums text-text-primary">
                      {star}
                    </span>
                    <span
                      className="h-2 w-28 overflow-hidden rounded-full bg-card-border sm:w-36"
                      aria-hidden="true"
                    >
                      <span
                        className={cn(
                          "block h-full rounded-full",
                          star === "1" || star === "2"
                            ? TONE_FILL.error
                            : star === "3"
                              ? TONE_FILL.warning
                              : TONE_FILL.success,
                        )}
                        style={{ width: `${(n / maxBar) * 100}%` }}
                      />
                    </span>
                    <span className="w-16 tabular-nums">
                      {n}
                      <span className="ml-1 text-text-tertiary">
                        {Math.round(share * 100)}%
                      </span>
                    </span>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>

        <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:content-start">
          <Stat
            label="Replied to"
            value={replyPct === null ? "—" : `${replyPct}%`}
            tone={shareTone(card.replied_share, 0.8, 0.6)}
            hint="of all reviews"
          />
          <Stat
            label="Typical reply time"
            value={
              card.median_reply_days === null
                ? "—"
                : `${card.median_reply_days} ${card.median_reply_days === 1 ? "day" : "days"}`
            }
            tone={daysTone(card.median_reply_days, 3, 7)}
            hint="median"
          />
          <Stat
            label="Last review"
            value={
              lastAge === null
                ? "—"
                : lastAge === 0
                  ? "today"
                  : `${lastAge} ${lastAge === 1 ? "day" : "days"} ago`
            }
            tone={daysTone(lastAge, 14, 30)}
            hint={card.last_review_date ?? undefined}
          />
          <Stat
            label="Low reviews unanswered"
            value={String(card.unanswered_critical_count)}
            tone={
              card.unanswered_critical_count === 0
                ? "success"
                : card.unanswered_critical_count < 3
                  ? "warning"
                  : "error"
            }
            hint="1 to 3 stars"
          />
        </dl>
      </div>

      {card.unanswered.length ? (
        <div className="mt-6 border-t border-card-border pt-5">
          <h3 className="text-sm font-semibold text-text-primary">
            Waiting for a reply
            <span className="ml-2 text-xs font-normal text-text-tertiary">
              newest first
            </span>
          </h3>
          <ul className="mt-3 space-y-3">
            {card.unanswered.map((review) => {
              const draft = drafts.get(review.id)?.suggestion;
              return (
                <li
                  key={review.id}
                  className="rounded-lg border border-card-border px-4 py-3"
                >
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-tertiary">
                    <span
                      className={cn(
                        "font-semibold",
                        review.rating !== null && review.rating <= 2
                          ? TONE_TEXT.error
                          : TONE_TEXT.warning,
                      )}
                    >
                      {review.rating === null
                        ? "Unrated"
                        : `${review.rating} star`}
                    </span>
                    <span>{review.date}</span>
                  </div>
                  <p className="mt-1 text-sm leading-6 text-text-primary">
                    {review.comment || "No comment left."}
                  </p>
                  {draft && typeof draft.value === "string" ? (
                    <div className="mt-3 rounded-md bg-background-gray-secondary px-3 py-2">
                      <p className="text-xs font-medium text-primary-500">
                        Drafted reply
                        <span className="ml-2 font-normal text-text-tertiary">
                          {draft.confidence} confidence · review before posting
                        </span>
                      </p>
                      <p className="mt-1 text-sm leading-6 whitespace-pre-line text-text-primary">
                        {draft.value}
                      </p>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </SectionCard>
  );
}
