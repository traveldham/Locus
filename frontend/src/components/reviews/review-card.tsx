"use client";

import { Button } from "@/components/tailgrids/core/button";
import { useRemoveReviewReplyMutation } from "@/hooks/use-reviews";
import type { Review } from "@/services/api/reviews";
import { cn } from "@/utils/cn";
import { formatDateTime } from "@/utils/format-date";
import { formatRelativeTime } from "@/utils/format-relative-time";
import { MapMarker5, Reply } from "@tailgrids/icons";
import Link from "next/link";
import { useState } from "react";
import { RemoveReplyDialog } from "./remove-reply-dialog";
import { ReplyComposer } from "./reply-composer";
import { ReviewChip } from "./review-chip";
import { reviewErrorMessage } from "./review-error-message";
import { StarRating } from "./star-rating";

/** Google withholds the name in two different ways, and they are worth telling apart. */
function reviewerName(review: Review) {
  if (review.is_anonymous) return "Anonymous";
  return review.reviewer_display_name ?? "Name not shared";
}

export interface ReviewCardProps {
  review: Review;
  className?: string;
}

export function ReviewCard({ review, className }: ReviewCardProps) {
  const [isComposing, setIsComposing] = useState(false);
  const [isConfirmingRemoval, setIsConfirmingRemoval] = useState(false);
  const removeReply = useRemoveReviewReplyMutation();

  const needsReply = !review.has_reply;
  const name = reviewerName(review);
  const postedAgo = formatRelativeTime(review.create_time);
  const postedAt = formatDateTime(review.create_time);
  const wasEdited = Boolean(review.update_time) && review.update_time !== review.create_time;
  const repliedAgo = formatRelativeTime(review.reply_update_time);
  const repliedAt = formatDateTime(review.reply_update_time);

  function handleRemove() {
    removeReply.mutate(review.id, {
      onSuccess: () => {
        setIsConfirmingRemoval(false);
        setIsComposing(false);
      },
    });
  }

  return (
    <article
      className={cn(
        "rounded-xl border border-card-border bg-card-background p-4 sm:p-5",
        needsReply && "border-l-[3px] border-l-primary-500",
        className,
      )}
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <StarRating rating={review.star_rating} showValue />
        {needsReply ? <ReviewChip tone="attention">Needs reply</ReviewChip> : null}
        <p className="ml-auto text-xs text-text-tertiary">
          <time dateTime={review.create_time} title={postedAt ?? undefined}>
            {postedAgo ?? postedAt ?? "Date not available"}
          </time>
          {wasEdited ? <span className="ml-2">· Edited by the reviewer</span> : null}
        </p>
      </div>

      <div className="mt-3 flex flex-wrap items-baseline gap-x-2.5 gap-y-1">
        <h3 className="text-sm font-semibold text-text-primary">{name}</h3>
        <span aria-hidden="true" className="text-text-disable">
          ·
        </span>
        <Link
          href={`/locations/${review.location_id}`}
          className="inline-flex items-center gap-1.5 text-sm text-text-secondary underline-offset-4 hover:text-text-primary hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
        >
          <MapMarker5 aria-hidden="true" focusable="false" className="size-3.5 shrink-0" />
          {review.location_title}
        </Link>
      </div>

      {review.comment ? (
        <p className="mt-3 text-sm leading-6 whitespace-pre-line text-text-primary">
          {review.comment}
        </p>
      ) : (
        <p className="mt-3 text-sm leading-6 text-text-tertiary italic">
          Rating only — {name} left no written review.
        </p>
      )}

      {/* While editing, the composer already holds this text — showing both would repeat it. */}
      {!isComposing && review.has_reply && review.reply_comment ? (
        <div className="mt-4 rounded-lg border-l-2 border-l-border-secondary-alt bg-background-gray-secondary py-3 pr-4 pl-3.5">
          <p className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs font-medium text-text-secondary">
            <Reply aria-hidden="true" focusable="false" className="size-3.5 shrink-0" />
            Your reply
            {repliedAgo ? (
              <span className="font-normal text-text-tertiary">
                ·{" "}
                <time dateTime={review.reply_update_time ?? undefined} title={repliedAt ?? undefined}>
                  published {repliedAgo}
                </time>
              </span>
            ) : null}
          </p>
          <p className="mt-1.5 text-sm leading-6 whitespace-pre-line text-text-primary">
            {review.reply_comment}
          </p>
        </div>
      ) : null}

      {isComposing ? (
        <ReplyComposer
          review={review}
          onClose={() => setIsComposing(false)}
          className="mt-4"
        />
      ) : (
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <Button
            size="xl"
            variant="primary"
            appearance={needsReply ? "fill" : "outline"}
            onPress={() => setIsComposing(true)}
          >
            <Reply aria-hidden="true" focusable="false" className="size-4" />
            {needsReply ? "Reply" : "Edit reply"}
            <span className="sr-only"> to {name}</span>
          </Button>
          {review.has_reply ? (
            <Button
              size="xl"
              variant="danger"
              appearance="ghost"
              onPress={() => setIsConfirmingRemoval(true)}
            >
              Remove reply
              <span className="sr-only"> to {name}</span>
            </Button>
          ) : null}
        </div>
      )}

      <RemoveReplyDialog
        isOpen={isConfirmingRemoval}
        onOpenChange={(open) => {
          setIsConfirmingRemoval(open);
          if (!open) removeReply.reset();
        }}
        reviewerName={name}
        locationTitle={review.location_title}
        onConfirm={handleRemove}
        isRemoving={removeReply.isPending}
        error={removeReply.isError ? reviewErrorMessage(removeReply.error, "remove_reply") : null}
      />
      <p
        className="mt-4 border-t border-card-border pt-3 text-xs text-text-tertiary tabular-nums"
        title={review.google_review_name ?? review.google_review_id}
      >
        Review ID: {review.google_review_id}
      </p>
    </article>
  );
}
