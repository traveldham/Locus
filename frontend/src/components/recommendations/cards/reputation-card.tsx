"use client";

import { SectionCard } from "@/components/common/section-card";
import { Button } from "@/components/tailgrids/core/button";
import { auditLatestKey } from "@/hooks/use-recommendations";
import { useReplyToReviewMutation } from "@/hooks/use-reviews";
import type { Recommendation } from "@/services/api/recommendations";
import { REPLY_MAX_LENGTH } from "@/services/api/reviews";
import { cn } from "@/utils/cn";
import { useQueryClient } from "@tanstack/react-query";
import { TONE_FILL, TONE_STROKE, TONE_TEXT } from "../audit-format";
import {
  replyDraftText,
  replySendErrorMessage,
  replyTargetId,
} from "../suggestion-panel";
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
            "motion-safe:transition-[stroke-dasharray] motion-safe:duration-500",
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

type UnansweredReview = ReputationCardData["unanswered"][number];

/**
 * One unanswered review, its drafted reply, and the button that publishes that reply.
 *
 * A mutation per row rather than one for the list: each send stands or falls on its own,
 * and a manager working down the list has to see which row failed, with that row's draft
 * still in front of them to retry.
 */
function UnansweredReviewRow({
  review,
  item,
  locationId,
}: {
  review: UnansweredReview;
  /** The finding that drafted a reply to this review, when one did. */
  item: Recommendation | undefined;
  locationId: string;
}) {
  const client = useQueryClient();
  const reply = useReplyToReviewMutation();
  const draft = item?.suggestion ?? null;
  const shown = typeof draft?.value === "string" ? draft.value : null;
  const targetId = item ? replyTargetId(item) : null;
  const publishable = replyDraftText(draft);
  const sent = reply.isSuccess;
  // A button that cannot publish is worse than no button, so the draft is shown either
  // way and the reason it cannot be sent is stated instead of being left to guess.
  const sendable =
    targetId && publishable ? { id: targetId, comment: publishable } : null;
  const blocked =
    shown === null || sendable
      ? null
      : !targetId
        ? "This finding does not name a review Locus can reply to, so this draft has to be posted from your Business Profile."
        : shown.trim().length > REPLY_MAX_LENGTH
          ? `Longer than Google's ${REPLY_MAX_LENGTH.toLocaleString()}-character reply limit, so it has to be shortened before it can be sent.`
          : null;

  function send() {
    if (!sendable || reply.isPending || sent) return;
    reply.mutate(sendable, {
      // The reviews cache is refreshed by the mutation itself. This audit is a stored
      // document that still calls the review unanswered, but its `inputs_changed` check
      // reads live rows, so refetching it is what surfaces the reply.
      onSuccess: () => {
        void client.invalidateQueries({ queryKey: auditLatestKey(locationId) });
      },
    });
  }

  return (
    <li className="border-b border-card-border py-4 last:border-b-0">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-text-tertiary">
        <span
          className={cn(
            "font-semibold",
            review.rating !== null && review.rating <= 2
              ? TONE_TEXT.error
              : TONE_TEXT.warning,
          )}
        >
          {review.rating === null ? "Unrated" : `${review.rating} star`}
        </span>
        <span>{review.date}</span>
      </div>
      <p className="mt-1 text-sm leading-6 text-text-primary">
        {review.comment || "No comment left."}
      </p>
      {draft && shown !== null ? (
        <div className="mt-3 rounded-md bg-background-gray-secondary px-3 py-2">
          <p className="text-xs font-medium text-primary-500">
            AI reply draft · {sent ? "sent to Google" : "not posted"}
            <span className="ml-2 font-normal text-text-tertiary">
              {draft.confidence} confidence · review before posting
            </span>
          </p>
          <p className="mt-1 text-sm leading-6 whitespace-pre-line text-text-primary">
            {shown}
          </p>
          {sendable ? (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <Button
                type="button"
                size="xl"
                onPress={send}
                isDisabled={reply.isPending || sent}
              >
                {sent
                  ? "Reply sent"
                  : reply.isPending
                    ? "Sending…"
                    : "Send this reply to Google"}
              </Button>
              <span className="text-xs leading-5 text-text-tertiary">
                Sends the text above word for word, published publicly on Google
                under your business name next to this review. Read it first.
              </span>
            </div>
          ) : blocked ? (
            <p className="mt-2 text-xs leading-5 text-text-tertiary">
              {blocked}
            </p>
          ) : null}
          {sent ? (
            <p role="status" className="mt-2 text-xs text-badge-success-text">
              Sent. This finding clears on the next audit.
            </p>
          ) : null}
          {reply.isError ? (
            <p
              role="alert"
              className="mt-2 rounded-lg bg-badge-error-background px-3 py-2 text-xs leading-5 text-badge-error-text"
            >
              {replySendErrorMessage(reply.error)}
            </p>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}

const THEME_RANK = { high: 0, medium: 1, low: 2 } as const;

/**
 * The one theme list to show, and how many findings drafted one.
 *
 * Three reputation checks each ask for this same list, so a weak rating that is also
 * falling produces three readings of the same review text. Printing all three would say
 * one thing three times, so the most confident speaks for them and the count says so.
 */
function themeDraft(items: Recommendation[]) {
  const drafted = items.filter(
    (i) =>
      i.suggestion?.field === "themes" &&
      Array.isArray(i.suggestion.value) &&
      i.suggestion.value.length > 0,
  );
  const ordered = [...drafted].sort(
    (a, b) =>
      THEME_RANK[a.suggestion?.confidence ?? "low"] -
        THEME_RANK[b.suggestion?.confidence ?? "low"] || b.score - a.score,
  );
  return { chosen: ordered[0] ?? null, total: ordered.length };
}

/** Reviews as a customer sees them, and the low reviews still waiting for a reply. */
export function ReputationCard({
  card: raw,
  items,
  location,
}: CategoryCardProps) {
  const card = raw as ReputationCardData;
  const drafts = new Map<string, Recommendation>();
  for (const item of items) {
    if (item.rule === "critical_review_unanswered" && item.subject)
      drafts.set(item.subject, item);
  }
  const themes = themeDraft(items);
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
      <p className="mb-5 max-w-prose text-sm leading-6 text-text-secondary">
        Understand your recorded customer feedback and which reviews still need
        a response. These figures use the reviews saved in this audit, which may
        differ from the live Google profile.
      </p>
      <div className="grid gap-6 xl:grid-cols-[auto_1fr]">
        <div className="flex flex-wrap items-center gap-5">
          <RatingRing average={card.average} />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-text-primary">
              {card.rated_count} rated{" "}
              {card.rated_count === 1 ? "review" : "reviews"}
            </p>
            <p className="mt-0.5 text-xs leading-5 text-text-secondary">
              {card.average === null
                ? "Not enough ratings to average."
                : "Average of the stored reviews with a valid star rating."}
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
                    <span className="w-10 text-right tabular-nums text-text-primary">
                      {star} star
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
                        style={{ width: `${share * 100}%` }}
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
            label="Latest recorded review"
            value={card.last_review_date ?? "Unknown"}
            tone="muted"
            hint="as saved in this audit"
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
            {card.unanswered.map((review) => (
              <UnansweredReviewRow
                key={review.id}
                review={review}
                item={drafts.get(review.id)}
                locationId={location.id}
              />
            ))}
          </ul>
        </div>
      ) : null}

      {themes.chosen && Array.isArray(themes.chosen.suggestion?.value) ? (
        <div className="mt-6 border-t border-card-border pt-5">
          <h3 className="text-sm font-semibold text-text-primary">
            What reviewers keep coming back to
            <span className="ml-2 text-xs font-normal text-text-tertiary">
              AI reading of the stored review text · nothing is published from
              here
            </span>
          </h3>
          <ul className="mt-3 flex flex-wrap gap-2">
            {themes.chosen.suggestion.value.map((theme) => (
              <li
                key={theme}
                className="rounded-lg border border-card-border px-3 py-1.5 text-sm text-text-primary"
              >
                {theme}
              </li>
            ))}
          </ul>
          <p className="mt-3 max-w-prose text-xs leading-5 text-text-secondary">
            {themes.chosen.suggestion.reason}
          </p>
          <p className="mt-1 text-xs leading-5 text-text-tertiary">
            Drafted for &ldquo;{themes.chosen.title}&rdquo;
            {themes.total > 1
              ? `, one of ${themes.total} findings that read the same reviews.`
              : "."}{" "}
            Read it as a lead to check, not a measured figure.
          </p>
        </div>
      ) : null}
    </SectionCard>
  );
}
