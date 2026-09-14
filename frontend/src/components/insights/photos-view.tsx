"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/tailgrids/core/button";
import { useMediaSummaryQuery } from "@/hooks/use-insights";
import { useLocationsQuery } from "@/hooks/use-locations";
import { LOCATIONS_MAX_PAGE_SIZE } from "@/services/api/locations";
import { cn } from "@/utils/cn";
import { MultipleImages } from "@tailgrids/icons";
import { useMemo, useState } from "react";
import { CardGridSkeleton } from "./insights-skeleton";
import { InsightsTabs } from "./insights-tabs";
import { LocationFilter } from "./location-filter";
import { PhotoCoverageCard } from "./photo-coverage-card";

export function PhotosView() {
  const [locationId, setLocationId] = useState<string | null>(null);
  const [onlyGaps, setOnlyGaps] = useState(false);

  const params = useMemo(() => ({ locationId: locationId ?? undefined }), [locationId]);

  const media = useMediaSummaryQuery(params);
  const locations = useLocationsQuery();

  const locationOptions = locations.data ?? [];
  const items = useMemo(() => media.data?.items ?? [], [media.data]);

  const missingCount = useMemo(
    () => items.filter((item) => !item.has_profile_photo || !item.has_cover_photo).length,
    [items],
  );

  const visibleItems = useMemo(
    () =>
      onlyGaps
        ? items.filter((item) => !item.has_profile_photo || !item.has_cover_photo)
        : items,
    [items, onlyGaps],
  );

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Photos"
        description="What Google holds on each profile: how many photos and videos, how they are categorised, and whether the profile and cover photos are set."
      />

      <InsightsTabs />

      <div className="flex flex-col gap-3 rounded-xl border border-card-border bg-card-background p-4 lg:flex-row lg:items-center">
        <div className="flex flex-col gap-1.5 lg:w-64">
          <LocationFilter
            value={locationId}
            onChange={setLocationId}
            locations={locationOptions}
            isLoading={locations.isPending}
            className="w-full"
          />
          {locationOptions.length === LOCATIONS_MAX_PAGE_SIZE ? (
            <p className="text-xs leading-5 text-text-tertiary">
              Lists the first {locationOptions.length.toLocaleString()} profiles.
            </p>
          ) : null}
        </div>

        <button
          type="button"
          aria-pressed={onlyGaps}
          onClick={() => setOnlyGaps((current) => !current)}
          className={cn(
            "flex h-11 items-center justify-center rounded-lg border px-4 text-sm font-medium transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
            onlyGaps
              ? "border-transparent bg-background-gray-secondary_alt_2 text-white-100"
              : "border-border-primary text-text-secondary hover:text-text-primary",
          )}
        >
          Only missing a profile or cover photo
        </button>
      </div>

      {media.isPending ? <CardGridSkeleton /> : null}

      {!media.isPending && media.isError ? (
        <div className="max-w-3xl">
          <ErrorState
            title="We could not load photo coverage"
            onRetry={() => void media.refetch()}
            isRetrying={media.isFetching}
          />
        </div>
      ) : null}

      {!media.isPending && !media.isError && items.length === 0 ? (
        <EmptyState
          icon={<MultipleImages aria-hidden="true" focusable="false" />}
          title="No photo data yet"
          description="Photo counts come from Google Business Profile. Nothing appears here until a profile has been imported and Google has returned its media."
        />
      ) : null}

      {!media.isPending && !media.isError && items.length > 0 ? (
        <div className="flex flex-col gap-5">
          <p className="text-sm leading-6 text-text-secondary">
            {missingCount === 0 ? (
              <>
                Every one of the {items.length.toLocaleString()}{" "}
                {items.length === 1 ? "profile" : "profiles"} below has both a profile photo and
                a cover photo set.
              </>
            ) : (
              <>
                <span className="font-semibold text-text-primary">
                  {missingCount.toLocaleString()}
                </span>{" "}
                of {items.length.toLocaleString()}{" "}
                {items.length === 1 ? "profile is" : "profiles are"} missing a profile photo or
                a cover photo. Those two are the images Google shows first.
              </>
            )}
          </p>

          {visibleItems.length === 0 ? (
            <EmptyState
              icon={<MultipleImages aria-hidden="true" focusable="false" />}
              title="Nothing is missing a photo"
              description="Every profile in this view has both a profile photo and a cover photo set."
              actions={
                <Button size="xl" appearance="outline" onPress={() => setOnlyGaps(false)}>
                  Show all profiles
                </Button>
              }
            />
          ) : (
            <div
              aria-busy={media.isFetching}
              className={cn(
                "grid gap-4 transition-opacity md:grid-cols-2 xl:grid-cols-3",
                media.isFetching && "opacity-60",
              )}
            >
              {visibleItems.map((item) => (
                <PhotoCoverageCard key={item.location_id} media={item} />
              ))}
            </div>
          )}

          <p className="text-xs leading-5 text-text-tertiary">
            Interior, exterior and team counts come from Google&rsquo;s own categorisation and
            do not have to add up to the photo total — anything Google has not categorised is
            shown separately as uncategorised.
          </p>
        </div>
      ) : null}
    </div>
  );
}
