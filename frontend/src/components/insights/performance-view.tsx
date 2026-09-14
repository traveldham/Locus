"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { PageHeader } from "@/components/common/page-header";
import { usePerformanceQuery } from "@/hooks/use-insights";
import { useLocationsQuery } from "@/hooks/use-locations";
import { LOCATIONS_MAX_PAGE_SIZE } from "@/services/api/locations";
import { BarChart2 } from "@tailgrids/icons";
import { useMemo, useState } from "react";
import { ActionsChart } from "./actions-chart";
import { DateRangeFilter, defaultDateRange, type DateRangeValue } from "./date-range-filter";
import { ImpressionsBreakdown } from "./impressions-breakdown";
import { InsightsTabs } from "./insights-tabs";
import { PerformanceSkeleton } from "./insights-skeleton";
import { LocationFilter } from "./location-filter";
import { PerformanceTotals } from "./performance-totals";
import { SourceMark } from "@/components/common/source-mark";

export function PerformanceView() {
  const [range, setRange] = useState<DateRangeValue>(defaultDateRange);
  const [locationId, setLocationId] = useState<string | null>(null);

  const params = useMemo(
    () => ({
      locationId: locationId ?? undefined,
      from: range.from,
      to: range.to,
    }),
    [locationId, range.from, range.to],
  );

  const performance = usePerformanceQuery(params);
  const locations = useLocationsQuery();

  const locationOptions = locations.data ?? [];
  const points = performance.data?.points ?? [];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Performance"
        description="How people found your profiles and what they did next, exactly as Google reported it."
        meta={performance.data ? <SourceMark source={performance.data.source} /> : null}
      />

      <InsightsTabs />

      {/* One filter row, scoping everything below it, so the figures always agree. */}
      <div className="flex flex-col gap-4 rounded-xl border border-card-border bg-card-background p-4 lg:flex-row lg:items-start lg:justify-between">
        <DateRangeFilter value={range} onChange={setRange} />
        <div className="flex flex-col gap-1.5 lg:items-end">
          <LocationFilter
            value={locationId}
            onChange={setLocationId}
            locations={locationOptions}
            isLoading={locations.isPending}
          />
          {locationOptions.length === LOCATIONS_MAX_PAGE_SIZE ? (
            <p className="text-xs leading-5 text-text-tertiary">
              Lists the first {locationOptions.length.toLocaleString()} profiles.
            </p>
          ) : null}
        </div>
      </div>

      {performance.isPending ? <PerformanceSkeleton /> : null}

      {!performance.isPending && performance.isError ? (
        <div className="max-w-3xl">
          <ErrorState
            title="We could not load performance"
            description="The request to Locus did not complete, so nothing below is showing. Check your connection, then try again."
            onRetry={() => void performance.refetch()}
            isRetrying={performance.isFetching}
          />
        </div>
      ) : null}

      {!performance.isPending && !performance.isError && points.length === 0 ? (
        <EmptyState
          icon={<BarChart2 aria-hidden="true" focusable="false" />}
          title="No performance data for this range"
          description="Google returned no daily reporting for the profiles and dates you selected. Widen the range, or check that the profile has been imported and synced."
          actions={
            <LinkButton href="/locations" appearance="outline">
              Review profiles
            </LinkButton>
          }
        />
      ) : null}

      {!performance.isPending &&
      !performance.isError &&
      points.length > 0 &&
      performance.data ? (
        <div className="flex flex-col gap-6">
          <PerformanceTotals totals={performance.data.totals} />
          <ActionsChart
            points={points}
            source={performance.data.source}
            isRefetching={performance.isFetching}
          />
          <ImpressionsBreakdown
            points={points}
            totals={performance.data.totals}
            source={performance.data.source}
            isRefetching={performance.isFetching}
          />
        </div>
      ) : null}
    </div>
  );
}
