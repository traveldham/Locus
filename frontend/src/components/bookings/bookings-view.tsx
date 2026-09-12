"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { SourceMark } from "@/components/common/source-mark";
import { Button } from "@/components/tailgrids/core/button";
import { useBookingCountQuery, useBookingsQuery } from "@/hooks/use-bookings";
import { useLocationsQuery } from "@/hooks/use-locations";
import { BOOKINGS_PAGE_SIZE, type BookingListParams } from "@/services/api/bookings";
import { LOCATIONS_MAX_PAGE_SIZE } from "@/services/api/locations";
import { cn } from "@/utils/cn";
import { CalendarTime } from "@tailgrids/icons";
import { useMemo, useState } from "react";
import { BookingsFilters, DEFAULT_BOOKING_FILTERS, isDefaultBookingFilters, type BookingFilterState } from "./bookings-filters";
import { BookingsPager } from "./bookings-pager";
import { BookingsSkeleton } from "./bookings-skeleton";
import { BookingsTable } from "./bookings-table";

export function BookingsView() {
  const [filters, setFilters] = useState<BookingFilterState>(DEFAULT_BOOKING_FILTERS);
  const [offset, setOffset] = useState(0);

  const listParams: BookingListParams = useMemo(
    () => ({
      locationId: filters.locationId ?? undefined,
      status: filters.status ?? undefined,
      bookingSource: filters.bookingSource ?? undefined,
      limit: BOOKINGS_PAGE_SIZE,
      offset,
    }),
    [filters, offset],
  );

  const bookings = useBookingsQuery(listParams);
  const locations = useLocationsQuery();

  // The same scope minus the source filter, so the Google figure does not change
  // meaning when someone narrows by source.
  const googleProfileCount = useBookingCountQuery({
    locationId: filters.locationId ?? undefined,
    status: filters.status ?? undefined,
    bookingSource: "google_profile",
  });

  const locationOptions = locations.data ?? [];
  const items = bookings.data?.items ?? [];
  const hasFilters = !isDefaultBookingFilters(filters);

  function updateFilters(patch: Partial<BookingFilterState>) {
    setFilters((current) => ({ ...current, ...patch }));
    setOffset(0);
  }

  function clearFilters() {
    setFilters(DEFAULT_BOOKING_FILTERS);
    setOffset(0);
  }

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <PageHeader
        title="Bookings"
        description="Every appointment request across your locations, and which channel it arrived through. Google reports only an aggregate count, so these individual records come from Locus."
        meta={<SourceMark source="locus" detail="Covers every booking on this page." />}
      />

      <div className="mt-6">
        <BookingsFilters
          filters={filters}
          onChange={updateFilters}
          onClear={clearFilters}
          locations={locationOptions}
          isLoadingLocations={locations.isPending}
          isLocationListPartial={locationOptions.length === LOCATIONS_MAX_PAGE_SIZE}
          googleProfileCount={googleProfileCount.data}
        />
      </div>

      <div className="mt-5">
        <SectionCard
          title="Booking requests"
          icon={<CalendarTime aria-hidden="true" focusable="false" />}
          actions={<SourceMark source="locus" />}
          bodyClassName="px-5 py-5"
        >
          {bookings.isPending ? <BookingsSkeleton /> : null}

          {!bookings.isPending && bookings.isError ? (
            <ErrorState
              title="We could not load your bookings"
              onRetry={() => void bookings.refetch()}
              isRetrying={bookings.isFetching}
            />
          ) : null}

          {!bookings.isPending && !bookings.isError && items.length === 0 ? (
            offset > 0 ? (
              <EmptyState
                icon={<CalendarTime aria-hidden="true" focusable="false" />}
                title="Nothing left on this page"
                description="The bookings that were here have moved since the page was loaded."
                actions={
                  <Button size="xl" onPress={() => setOffset(0)}>
                    Back to the first page
                  </Button>
                }
                className="border-0 bg-transparent py-8"
              />
            ) : hasFilters ? (
              <EmptyState
                icon={<CalendarTime aria-hidden="true" focusable="false" />}
                title="No bookings match these filters"
                description="No booking in this organization matches the filters you have set. Widen them to see more."
                actions={
                  <Button size="xl" appearance="outline" onPress={clearFilters}>
                    Clear filters
                  </Button>
                }
                className="border-0 bg-transparent py-8"
              />
            ) : (
              <EmptyState
                icon={<CalendarTime aria-hidden="true" focusable="false" />}
                title="No bookings yet"
                description="Bookings arrive from your website, your Google listing, the phone and walk-ins. Nothing appears here until the first request is recorded."
                className="border-0 bg-transparent py-8"
              />
            )
          ) : null}

          {!bookings.isPending && !bookings.isError && items.length > 0 ? (
            <div className="flex flex-col gap-5">
              <div
                aria-busy={bookings.isFetching}
                className={cn("transition-opacity", bookings.isFetching && "opacity-60")}
              >
                <BookingsTable bookings={items} showLocation={filters.locationId === null} />
              </div>

              <BookingsPager
                offset={bookings.data?.offset ?? offset}
                limit={bookings.data?.limit ?? BOOKINGS_PAGE_SIZE}
                total={bookings.data?.total ?? items.length}
                count={items.length}
                onOffsetChange={setOffset}
                isFetching={bookings.isFetching}
              />
            </div>
          ) : null}
        </SectionCard>
      </div>
    </div>
  );
}
