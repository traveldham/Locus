"use client";

import { usePostsQuery } from "@/hooks/use-posts";
import { useReviewsQuery } from "@/hooks/use-reviews";
import { useState } from "react";
import { humanizeToken } from "../hours-model";

export const previewControl =
  "inline-flex min-h-11 min-w-11 items-center justify-center gap-2 rounded-full border border-card-border px-4 py-2 text-sm font-medium text-text-primary transition-colors hover:bg-background-gray-secondary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500 disabled:cursor-not-allowed disabled:opacity-50";

export function RatingStars({ rating }: { rating: number }) {
  return (
    <span
      className="inline-flex gap-0.5 text-badge-warning-text"
      aria-label={`${rating.toFixed(1)} out of 5 stars`}
    >
      {[1, 2, 3, 4, 5].map((star) => (
        <svg
          key={star}
          aria-hidden="true"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill={star <= Math.round(rating) ? "currentColor" : "none"}
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <path d="m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9Z" />
        </svg>
      ))}
    </span>
  );
}

function dateLabel(value: string | null) {
  if (!value) return "Date unavailable";
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}

function Pages({
  offset,
  total,
  busy,
  setOffset,
}: {
  offset: number;
  total: number;
  busy: boolean;
  setOffset: (offset: number) => void;
}) {
  return (
    <div className="mt-5 flex flex-wrap items-center justify-between gap-3 text-sm text-text-secondary">
      <span>
        {total
          ? `${offset + 1}–${Math.min(offset + 5, total)} of ${total}`
          : "No records"}
      </span>
      <div className="flex gap-2">
        <button
          className={previewControl}
          disabled={offset === 0 || busy}
          onClick={() => setOffset(offset - 5)}
        >
          Previous
        </button>
        <button
          className={previewControl}
          disabled={offset + 5 >= total || busy}
          onClick={() => setOffset(offset + 5)}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export function PreviewReviews({ locationId }: { locationId: string }) {
  const [offset, setOffset] = useState(0);
  const query = useReviewsQuery({ locationId, offset, limit: 5 });
  return (
    <section aria-label="Customer reviews">
      <h3 className="text-lg font-semibold text-text-primary">Reviews</h3>
      <p className="mt-1 text-sm text-text-secondary">
        Newest first · stored reviews, not a live Google feed.
      </p>
      {query.isPending ? (
        <p role="status" className="py-6">
          Loading reviews…
        </p>
      ) : null}
      {query.isError ? (
        <button
          className={`${previewControl} mt-4`}
          onClick={() => void query.refetch()}
        >
          Reviews unavailable. Retry
        </button>
      ) : null}
      {query.data?.items.map((review) => (
        <article key={review.id} className="border-b border-card-border py-5">
          <div className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className="flex size-10 shrink-0 items-center justify-center rounded-full bg-background-gray-secondary font-semibold text-text-secondary"
            >
              {review.is_anonymous
                ? "A"
                : (review.reviewer_display_name?.[0] ?? "R")}
            </span>
            <div>
              <h4 className="font-medium text-text-primary">
                {review.is_anonymous
                  ? "Anonymous reviewer"
                  : review.reviewer_display_name || "Reviewer"}
              </h4>
              <p className="text-xs text-text-secondary">
                {dateLabel(review.create_time)}
              </p>
            </div>
          </div>
          <div className="mt-3">
            <RatingStars rating={review.star_rating} />
          </div>
          <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-text-primary">
            {review.comment || "This review has a rating only."}
          </p>
          {review.reply_comment ? (
            <div className="mt-4 rounded-lg bg-background-gray-secondary p-4 text-sm">
              <p className="font-medium text-text-primary">
                Response from the owner
              </p>
              <p className="mt-1 text-xs text-text-secondary">
                {dateLabel(review.reply_update_time)}
              </p>
              <p className="mt-2 whitespace-pre-wrap break-words leading-6 text-text-secondary">
                {review.reply_comment}
              </p>
            </div>
          ) : null}
        </article>
      ))}
      {query.data ? (
        <Pages
          offset={offset}
          total={query.data.total}
          busy={query.isFetching}
          setOffset={setOffset}
        />
      ) : null}
    </section>
  );
}

export function PreviewPosts({ locationId }: { locationId: string }) {
  const [offset, setOffset] = useState(0);
  const query = usePostsQuery({ locationId, offset, limit: 5 });
  return (
    <section aria-label="Business updates">
      <h3 className="text-lg font-semibold text-text-primary">
        Updates from this business
      </h3>
      {query.isPending ? (
        <p role="status" className="py-6">
          Loading updates…
        </p>
      ) : null}
      {query.isError ? (
        <button
          className={`${previewControl} mt-4`}
          onClick={() => void query.refetch()}
        >
          Updates unavailable. Retry
        </button>
      ) : null}
      {query.data?.items.map((post) => (
        <article key={post.id} className="border-b border-card-border py-5">
          <p className="text-xs text-text-secondary">
            {humanizeToken(post.post_type)} · {dateLabel(post.published_on)}
          </p>
          <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-6 text-text-primary">
            {post.summary || "Post text not available."}
          </p>
          {post.cta_type ? (
            <p className="mt-3 text-xs text-text-secondary">
              Recorded action: {humanizeToken(post.cta_type)} · destination URL
              not supplied
            </p>
          ) : null}
        </article>
      ))}
      {query.data ? (
        <Pages
          offset={offset}
          total={query.data.total}
          busy={query.isFetching}
          setOffset={setOffset}
        />
      ) : null}
    </section>
  );
}
