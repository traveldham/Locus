"use client";

import { Button } from "@/components/tailgrids/core/button";
import { ArrowLeft, ArrowRight } from "@tailgrids/icons";

export interface ReviewsPagerProps {
  /** Index of the first review on this page, zero based. */
  offset: number;
  limit: number;
  total: number;
  /** Reviews actually returned for this page. */
  count: number;
  onOffsetChange: (offset: number) => void;
  isFetching: boolean;
}

export function ReviewsPager({
  offset,
  limit,
  total,
  count,
  onOffsetChange,
  isFetching,
}: ReviewsPagerProps) {
  const first = total === 0 ? 0 : offset + 1;
  const last = offset + count;
  const page = Math.floor(offset / limit) + 1;
  const pageCount = Math.max(1, Math.ceil(total / limit));
  const hasPrevious = offset > 0;
  const hasNext = last < total;

  if (total <= limit && !hasPrevious) return null;

  return (
    <nav
      aria-label="Review pages"
      className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3"
    >
      <p aria-live="polite" className="text-sm text-text-tertiary tabular-nums">
        Showing{" "}
        <span className="font-medium text-text-primary">
          {first.toLocaleString()}–{last.toLocaleString()}
        </span>{" "}
        of {total.toLocaleString()} {total === 1 ? "review" : "reviews"}
        <span className="sr-only">
          . Page {page} of {pageCount}.
        </span>
      </p>

      <div className="flex items-center gap-2">
        <Button
          size="xl"
          appearance="outline"
          isDisabled={!hasPrevious || isFetching}
          onPress={() => onOffsetChange(Math.max(0, offset - limit))}
        >
          <ArrowLeft aria-hidden="true" focusable="false" className="size-4" />
          Previous
          <span className="sr-only"> page of reviews</span>
        </Button>
        <Button
          size="xl"
          appearance="outline"
          isDisabled={!hasNext || isFetching}
          onPress={() => onOffsetChange(offset + limit)}
        >
          Next
          <span className="sr-only"> page of reviews</span>
          <ArrowRight aria-hidden="true" focusable="false" className="size-4" />
        </Button>
      </div>
    </nav>
  );
}
