"use client";

import {
  Select,
  SelectContent,
  SelectIndicator,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/tailgrids/core/select";
import {
  BOOKING_SOURCES,
  BOOKING_STATUSES,
  bookingSourceLabel,
  bookingStatusLabel,
  type BookingSource,
  type BookingStatus,
} from "@/services/api/bookings";
import type { LocationSummary } from "@/services/api/locations";

const ANY_LOCATION = "__any_location__";
const ANY_STATUS = "__any_status__";
const ANY_SOURCE = "__any_source__";

export interface BookingFilterState {
  locationId: string | null;
  status: BookingStatus | null;
  bookingSource: BookingSource | null;
}

export const DEFAULT_BOOKING_FILTERS: BookingFilterState = {
  locationId: null,
  status: null,
  bookingSource: null,
};

export function isDefaultBookingFilters(filters: BookingFilterState) {
  return (
    filters.locationId === null &&
    filters.status === null &&
    filters.bookingSource === null
  );
}

export interface BookingsFiltersProps {
  filters: BookingFilterState;
  onChange: (patch: Partial<BookingFilterState>) => void;
  onClear: () => void;
  locations: LocationSummary[];
  isLoadingLocations: boolean;
  /** True when the API returned a full page, so the list below is not every location. */
  isLocationListPartial?: boolean;
  /**
   * Bookings from the Google listing within the other active filters, straight from
   * the API's own total — the number the product exists to move.
   */
  googleProfileCount?: number;
}

export function BookingsFilters({
  filters,
  onChange,
  onClear,
  locations,
  isLoadingLocations,
  isLocationListPartial = false,
  googleProfileCount,
}: BookingsFiltersProps) {
  const hasFilters = !isDefaultBookingFilters(filters);

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-card-border bg-card-background p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <Select
          aria-label="Filter by location"
          value={filters.locationId ?? ANY_LOCATION}
          onChange={(key: string) =>
            onChange({ locationId: key === ANY_LOCATION ? null : key })
          }
          isDisabled={isLoadingLocations && locations.length === 0}
          className="w-full lg:max-w-64"
        >
          <SelectTrigger size="xl" className="w-full">
            <SelectValue />
            <SelectIndicator />
          </SelectTrigger>
          <SelectContent className="max-h-72">
            <SelectItem id={ANY_LOCATION}>All locations</SelectItem>
            {locations.map((location) => (
              <SelectItem key={location.id} id={location.id} textValue={location.title}>
                {location.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          aria-label="Filter by status"
          value={filters.status ?? ANY_STATUS}
          onChange={(key: string) =>
            onChange({ status: key === ANY_STATUS ? null : (key as BookingStatus) })
          }
          className="w-full lg:max-w-48"
        >
          <SelectTrigger size="xl" className="w-full">
            <SelectValue />
            <SelectIndicator />
          </SelectTrigger>
          <SelectContent>
            <SelectItem id={ANY_STATUS}>Any status</SelectItem>
            {BOOKING_STATUSES.map((status) => (
              <SelectItem key={status} id={status} textValue={bookingStatusLabel(status)}>
                {bookingStatusLabel(status)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          aria-label="Filter by booking source"
          value={filters.bookingSource ?? ANY_SOURCE}
          onChange={(key: string) =>
            onChange({
              bookingSource: key === ANY_SOURCE ? null : (key as BookingSource),
            })
          }
          className="w-full lg:max-w-52"
        >
          <SelectTrigger size="xl" className="w-full">
            <SelectValue />
            <SelectIndicator />
          </SelectTrigger>
          <SelectContent>
            <SelectItem id={ANY_SOURCE}>Any source</SelectItem>
            {BOOKING_SOURCES.map((source) => (
              <SelectItem key={source} id={source} textValue={bookingSourceLabel(source)}>
                {bookingSourceLabel(source)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {hasFilters ? (
          <button
            type="button"
            onClick={onClear}
            className="flex h-11 shrink-0 items-center justify-center rounded-lg px-3 text-sm font-medium text-text-secondary underline decoration-border-secondary-alt underline-offset-4 transition outline-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-primary-500"
          >
            Clear filters
          </button>
        ) : null}
      </div>

      {googleProfileCount !== undefined ? (
        <p className="text-sm leading-5 text-text-tertiary">
          <button
            type="button"
            onClick={() => onChange({ bookingSource: "google_profile" })}
            aria-pressed={filters.bookingSource === "google_profile"}
            className="inline-flex min-h-11 items-center rounded-lg px-1 font-medium text-text-secondary underline decoration-border-secondary-alt underline-offset-4 transition outline-none hover:text-text-primary focus-visible:ring-2 focus-visible:ring-primary-500"
          >
            {googleProfileCount.toLocaleString()}{" "}
            {googleProfileCount === 1 ? "booking came" : "bookings came"} from your Google
            listing
          </button>{" "}
          within these filters.
        </p>
      ) : null}

      {isLocationListPartial ? (
        <p className="text-xs leading-5 text-text-tertiary">
          The location filter lists the first {locations.length.toLocaleString()} locations in
          this organization.
        </p>
      ) : null}
    </div>
  );
}
