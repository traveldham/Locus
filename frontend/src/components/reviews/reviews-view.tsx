"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/tailgrids/core/button";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useLocationsQuery } from "@/hooks/use-locations";
import {
  useReviewsQuery,
  useSyncReviewsMutation,
  useUnrepliedReviewCountQuery,
} from "@/hooks/use-reviews";
import { LOCATIONS_MAX_PAGE_SIZE } from "@/services/api/locations";
import { REVIEWS_PAGE_SIZE, type ReviewListParams } from "@/services/api/reviews";
import { cn } from "@/utils/cn";
import { Comment1 } from "@tailgrids/icons";
import { useMemo, useState } from "react";
import { ReviewCard } from "./review-card";
import { reviewErrorMessage } from "./review-error-message";
import {
  DEFAULT_REVIEW_FILTERS,
  isDefaultReviewFilters,
  ReviewFilters,
  type ReviewFilterState,
} from "./review-filters";
import { ReviewsPager } from "./reviews-pager";
import { ReviewsSkeleton } from "./reviews-skeleton";
import { SyncReviewsButton } from "./sync-reviews-button";

function repliedParam(replied: ReviewFilterState["replied"]) {
  if (replied === "all") return undefined;
  return replied === "replied";
}

export function ReviewsView() {
  const [filters, setFilters] = useState<ReviewFilterState>(DEFAULT_REVIEW_FILTERS);
  const [offset, setOffset] = useState(0);

  // The search box drives a server query, so it settles before a request is sent.
  const debouncedSearch = useDebouncedValue(filters.search, 300);
  const searchTerm = debouncedSearch.trim();

  const scope = useMemo(
    () => ({
      locationId: filters.locationId ?? undefined,
      rating: filters.rating ?? undefined,
      q: searchTerm || undefined,
    }),
    [filters.locationId, filters.rating, searchTerm],
  );

  const listParams: ReviewListParams = useMemo(
    () => ({
      ...scope,
      replied: repliedParam(filters.replied),
      limit: REVIEWS_PAGE_SIZE,
      offset,
    }),
    [scope, filters.replied, offset],
  );

  const reviews = useReviewsQuery(listParams);
  const unrepliedCount = useUnrepliedReviewCountQuery(scope);
  const locations = useLocationsQuery();
  const sync = useSyncReviewsMutation();

  const locationOptions = locations.data ?? [];
  const items = reviews.data?.items ?? [];
  const hasFilters = !isDefaultReviewFilters(filters);

  function updateFilters(patch: Partial<ReviewFilterState>) {
    setFilters((current) => ({ ...current, ...patch }));
    setOffset(0);
  }

  function clearFilters() {
    setFilters(DEFAULT_REVIEW_FILTERS);
    setOffset(0);
  }

  function handleSync() {
    sync.mutate({ location_id: filters.locationId ?? undefined });
  }

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <PageHeader
        title="Reviews"
        description="Every Google review across your locations, with the replies you have published under your business name."
        actions={<SyncReviewsButton onSync={handleSync} isSyncing={sync.isPending} />}
      />

      {sync.isSuccess ? (
        <p
          role="status"
          className="mt-6 rounded-lg bg-badge-success-background px-3.5 py-2.5 text-sm leading-5 text-badge-success-text"
        >
          Synced {sync.data.total} review{sync.data.total === 1 ? "" : "s"} from{" "}
          {sync.data.locations_synced} location{sync.data.locations_synced === 1 ? "" : "s"}.
        </p>
      ) : null}

      {sync.isError ? (
        <p
          role="alert"
          className="mt-6 rounded-lg bg-badge-error-background px-3.5 py-2.5 text-sm leading-5 text-badge-error-text"
        >
          {reviewErrorMessage(sync.error, "sync")}
        </p>
      ) : null}

      <div className="mt-6">
        <ReviewFilters
          filters={filters}
          onChange={updateFilters}
          onClear={clearFilters}
          locations={locationOptions}
          isLoadingLocations={locations.isPending}
          isLocationListPartial={locationOptions.length === LOCATIONS_MAX_PAGE_SIZE}
          unrepliedCount={unrepliedCount.data}
        />
      </div>

      <div className="mt-5">
        {reviews.isPending ? <ReviewsSkeleton /> : null}

        {!reviews.isPending && reviews.isError ? (
          <div className="max-w-3xl">
            <ErrorState
              title="We could not load your reviews"
              onRetry={() => void reviews.refetch()}
              isRetrying={reviews.isFetching}
            />
          </div>
        ) : null}

        {!reviews.isPending && !reviews.isError && items.length === 0 ? (
          offset > 0 ? (
            <EmptyState
              icon={<Comment1 aria-hidden="true" focusable="false" />}
              title="Nothing left on this page"
              description="The reviews that were here have moved since the page was loaded — replying to a review can take it out of the current view."
              actions={
                <Button size="xl" onPress={() => setOffset(0)}>
                  Back to the first page
                </Button>
              }
            />
          ) : hasFilters ? (
            <EmptyState
              icon={<Comment1 aria-hidden="true" focusable="false" />}
              title={
                filters.replied === "unreplied"
                  ? "Nothing is waiting on a reply"
                  : "No reviews match these filters"
              }
              description={
                filters.replied === "unreplied"
                  ? "Every review that matches these filters already has a reply from you."
                  : "No review in this organization matches the filters you have set. Widen them to see more."
              }
              actions={
                <Button size="xl" appearance="outline" onPress={clearFilters}>
                  Clear filters
                </Button>
              }
            />
          ) : (
            <EmptyState
              icon={<Comment1 aria-hidden="true" focusable="false" />}
              title="No reviews yet"
              description="Reviews are imported from Google Business Profile. Sync to pull in what your locations have already received; nothing appears here until Google returns it."
              actions={
                <>
                  <SyncReviewsButton
                    onSync={handleSync}
                    isSyncing={sync.isPending}
                    appearance="fill"
                  />
                  <LinkButton href="/settings/integrations" appearance="outline">
                    Check Google connection
                  </LinkButton>
                </>
              }
            />
          )
        ) : null}

        {!reviews.isPending && !reviews.isError && items.length > 0 ? (
          <div className="flex flex-col gap-5">
            <div
              aria-busy={reviews.isFetching}
              className={cn(
                "flex flex-col gap-3 transition-opacity",
                reviews.isFetching && "opacity-60",
              )}
            >
              {items.map((review) => (
                <ReviewCard key={review.id} review={review} />
              ))}
            </div>

            <ReviewsPager
              offset={reviews.data?.offset ?? offset}
              limit={reviews.data?.limit ?? REVIEWS_PAGE_SIZE}
              total={reviews.data?.total ?? items.length}
              count={items.length}
              onOffsetChange={setOffset}
              isFetching={reviews.isFetching}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
