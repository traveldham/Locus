"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { Button } from "@/components/tailgrids/core/button";
import {
  Select,
  SelectContent,
  SelectIndicator,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/tailgrids/core/select";
import { useSearchTermsQuery } from "@/hooks/use-insights";
import { useLocationsQuery } from "@/hooks/use-locations";
import { SEARCH_TERMS_PAGE_SIZE, type DataSource } from "@/services/api/insights";
import { LOCATIONS_MAX_PAGE_SIZE } from "@/services/api/locations";
import { cn } from "@/utils/cn";
import { Search1 } from "@tailgrids/icons";
import { format, subMonths } from "date-fns";
import { useMemo, useState } from "react";
import { formatReportingMonth } from "./chart-series";
import { InsightsPager } from "./insights-pager";
import { TableSkeleton } from "./insights-skeleton";
import { InsightsTabs } from "./insights-tabs";
import { LocationFilter } from "./location-filter";
import { SearchTermsTable } from "./search-terms-table";
import { SourceMark } from "@/components/common/source-mark";

const ALL_MONTHS = "__all_months__";

/** Google reports search terms by calendar month, so the filter offers months. */
function recentMonths(count = 12) {
  const today = new Date();
  return Array.from({ length: count }, (_, index) =>
    format(subMonths(today, index), "yyyy-MM"),
  );
}

export function SearchTermsView() {
  const [yearMonth, setYearMonth] = useState<string | null>(null);
  const [locationId, setLocationId] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);

  const monthOptions = useMemo(() => recentMonths(), []);

  const params = useMemo(
    () => ({
      locationId: locationId ?? undefined,
      yearMonth: yearMonth ?? undefined,
      limit: SEARCH_TERMS_PAGE_SIZE,
      offset,
    }),
    [locationId, yearMonth, offset],
  );

  const searchTerms = useSearchTermsQuery(params);
  const locations = useLocationsQuery();

  const locationOptions = locations.data ?? [];
  const items = useMemo(() => searchTerms.data?.items ?? [], [searchTerms.data]);
  const hasFilters = yearMonth !== null || locationId !== null;

  const sources = useMemo(() => {
    const seen = new Set<DataSource>();
    for (const term of items) seen.add(term.source);
    return [...seen];
  }, [items]);

  function clearFilters() {
    setYearMonth(null);
    setLocationId(null);
    setOffset(0);
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Search terms"
        description="The queries people typed before Google showed them your profile, with the impressions each one earned."
      />

      <InsightsTabs />

      <div className="flex flex-col gap-3 rounded-xl border border-card-border bg-card-background p-4 lg:flex-row lg:items-center">
        <Select
          aria-label="Filter by reporting month"
          value={yearMonth ?? ALL_MONTHS}
          onChange={(key: string) => {
            setYearMonth(key === ALL_MONTHS ? null : key);
            setOffset(0);
          }}
          className="w-full lg:max-w-56"
        >
          <SelectTrigger size="xl" className="w-full">
            <SelectValue />
            <SelectIndicator />
          </SelectTrigger>
          <SelectContent className="max-h-72">
            <SelectItem id={ALL_MONTHS}>All months</SelectItem>
            {monthOptions.map((month) => (
              <SelectItem key={month} id={month} textValue={formatReportingMonth(month)}>
                {formatReportingMonth(month)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <div className="flex flex-col gap-1.5 lg:w-64">
          <LocationFilter
            value={locationId}
            onChange={(next) => {
              setLocationId(next);
              setOffset(0);
            }}
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

        {hasFilters ? (
          <button
            type="button"
            onClick={clearFilters}
            className="flex h-11 shrink-0 items-center justify-center rounded-lg px-3 text-sm font-medium text-text-secondary underline decoration-border-secondary-alt underline-offset-4 transition outline-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-primary-500"
          >
            Clear filters
          </button>
        ) : null}
      </div>

      {searchTerms.isPending ? <TableSkeleton label="Loading search terms" /> : null}

      {!searchTerms.isPending && searchTerms.isError ? (
        <div className="max-w-3xl">
          <ErrorState
            title="We could not load search terms"
            onRetry={() => void searchTerms.refetch()}
            isRetrying={searchTerms.isFetching}
          />
        </div>
      ) : null}

      {!searchTerms.isPending && !searchTerms.isError && items.length === 0 ? (
        offset > 0 ? (
          <EmptyState
            icon={<Search1 aria-hidden="true" focusable="false" />}
            title="Nothing left on this page"
            description="The terms that were here have moved since the page was loaded."
            actions={
              <Button size="xl" onPress={() => setOffset(0)}>
                Back to the first page
              </Button>
            }
          />
        ) : (
          <EmptyState
            icon={<Search1 aria-hidden="true" focusable="false" />}
            title={hasFilters ? "No search terms match these filters" : "No search terms yet"}
            description={
              hasFilters
                ? "Google reported no search terms for the month and profile you selected. Widen the filters to see more."
                : "Search terms are imported from Google Business Profile once a reporting month closes. Nothing appears here until Google returns it."
            }
            actions={
              hasFilters ? (
                <Button size="xl" appearance="outline" onPress={clearFilters}>
                  Clear filters
                </Button>
              ) : null
            }
          />
        )
      ) : null}

      {!searchTerms.isPending && !searchTerms.isError && items.length > 0 ? (
        <SectionCard
          title={
            yearMonth ? `Search terms · ${formatReportingMonth(yearMonth)}` : "Search terms"
          }
          icon={<Search1 aria-hidden="true" focusable="false" />}
          bodyClassName="px-0 py-0"
          actions={
            <div className="flex flex-wrap gap-1.5">
              {sources.map((source) => (
                <SourceMark key={source} source={source} />
              ))}
            </div>
          }
        >
          <div
            aria-busy={searchTerms.isFetching}
            className={cn("transition-opacity", searchTerms.isFetching && "opacity-60")}
          >
            <SearchTermsTable
              items={items}
              hideMonth={yearMonth !== null}
              hideLocation={locationId !== null}
            />
          </div>

          <p className="border-t border-card-border px-5 py-4 text-xs leading-5 text-text-tertiary">
            Terms are ordered by impressions, highest first. Where a figure reads{" "}
            <span className="font-medium text-text-secondary">&lt;</span> a number, Google
            withheld the exact count because the term was searched too few times to report
            without identifying individual searchers. The real figure is below that bound;
            Locus does not estimate it.
          </p>

          <div className="border-t border-card-border px-5 py-4">
            <InsightsPager
              offset={searchTerms.data?.offset ?? offset}
              limit={searchTerms.data?.limit ?? SEARCH_TERMS_PAGE_SIZE}
              total={searchTerms.data?.total ?? items.length}
              count={items.length}
              onOffsetChange={setOffset}
              isFetching={searchTerms.isFetching}
              noun="term"
              pluralNoun="terms"
              label="Search term pages"
            />
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}
