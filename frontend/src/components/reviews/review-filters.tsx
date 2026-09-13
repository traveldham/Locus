"use client";

import { Input } from "@/components/tailgrids/core/input";
import {
  Select,
  SelectContent,
  SelectIndicator,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/tailgrids/core/select";
import { TextField } from "@/components/tailgrids/core/text-field";
import type { LocationSummary } from "@/services/api/locations";
import { REVIEW_STAR_RATINGS } from "@/services/api/reviews";
import { cn } from "@/utils/cn";
import { Close, Search1 } from "@tailgrids/icons";

export type RepliedFilter = "unreplied" | "all" | "replied";

export interface ReviewFilterState {
  replied: RepliedFilter;
  locationId: string | null;
  rating: number | null;
  search: string;
}

export const DEFAULT_REVIEW_FILTERS: ReviewFilterState = {
  replied: "all",
  locationId: null,
  rating: null,
  search: "",
};

export function isDefaultReviewFilters(filters: ReviewFilterState) {
  return (
    filters.replied === DEFAULT_REVIEW_FILTERS.replied &&
    filters.locationId === null &&
    filters.rating === null &&
    filters.search.trim().length === 0
  );
}

const ANY_LOCATION = "__any_location__";
const ANY_RATING = "__any_rating__";

/** Short labels keep all three legible side by side on a phone; the group is labelled. */
const REPLIED_OPTIONS: {
  id: RepliedFilter;
  label: string;
  description: string;
}[] = [
  {
    id: "unreplied",
    label: "Needs reply",
    description: "Reviews with no reply yet",
  },
  { id: "all", label: "All", description: "All reviews" },
  {
    id: "replied",
    label: "Replied",
    description: "Reviews you have replied to",
  },
];

export interface ReviewFiltersProps {
  filters: ReviewFilterState;
  onChange: (patch: Partial<ReviewFilterState>) => void;
  onClear: () => void;
  locations: LocationSummary[];
  isLoadingLocations: boolean;
  /** True when the API returned a full page, so the list below is not every location. */
  isLocationListPartial?: boolean;
  /** Full filtered totals, not the number of reviews on the current page. */
  counts?: Record<RepliedFilter, number>;
}

export function ReviewFilters({
  filters,
  onChange,
  onClear,
  locations,
  isLoadingLocations,
  isLocationListPartial = false,
  counts,
}: ReviewFiltersProps) {
  const hasFilters = !isDefaultReviewFilters(filters);

  return (
    <div className="flex flex-col gap-4 rounded-xl border border-card-border bg-card-background p-4">
      <div
        role="group"
        aria-label="Reply status"
        className="flex w-full gap-1 rounded-lg bg-background-gray-secondary p-1 sm:w-auto sm:self-start"
      >
        {REPLIED_OPTIONS.map((option) => {
          const isActive = filters.replied === option.id;
          const count = counts?.[option.id];

          return (
            <button
              key={option.id}
              type="button"
              aria-pressed={isActive}
              aria-label={
                count !== undefined
                  ? `${option.description}: ${count.toLocaleString()}`
                  : option.description
              }
              onClick={() => onChange({ replied: option.id })}
              className={cn(
                "flex min-h-11 flex-1 flex-col items-center justify-center gap-1 rounded-md px-2 py-2 text-sm font-medium whitespace-nowrap transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500 sm:flex-none sm:flex-row sm:gap-2 sm:px-4",
                isActive
                  ? "bg-background-gray-secondary_alt_2 text-white-100"
                  : "text-text-secondary hover:text-text-primary",
              )}
            >
              {option.label}
              {count !== undefined ? (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-xs leading-4 font-semibold tabular-nums",
                    isActive
                      ? "bg-white-100/20 text-white-100"
                      : "bg-badge-warning-background text-badge-warning-text",
                  )}
                >
                  {count.toLocaleString()}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
        <TextField
          aria-label="Search reviews"
          value={filters.search}
          onChange={(search) => onChange({ search })}
          className="relative w-full lg:max-w-sm"
        >
          <Search1
            aria-hidden="true"
            focusable="false"
            className="pointer-events-none absolute top-1/2 left-3.5 size-4 -translate-y-1/2 text-icon-tertiary"
          />
          <Input
            type="search"
            placeholder="Search reviewer or review text"
            className="h-11 w-full pr-12 pl-10"
          />
          {filters.search ? (
            <button
              type="button"
              onClick={() => onChange({ search: "" })}
              className="absolute top-1/2 right-1 flex size-11 -translate-y-1/2 items-center justify-center rounded-lg text-icon-tertiary transition outline-none hover:text-icon-primary focus-visible:ring-2 focus-visible:ring-primary-500 [&>svg]:size-4"
            >
              <Close aria-hidden="true" focusable="false" />
              <span className="sr-only">Clear search</span>
            </button>
          ) : null}
        </TextField>

        <Select
          aria-label="Filter by location"
          value={filters.locationId ?? ANY_LOCATION}
          onChange={(key: string) =>
            onChange({ locationId: key === ANY_LOCATION ? null : key })
          }
          isDisabled={isLoadingLocations && locations.length === 0}
          className="w-full lg:max-w-56"
        >
          <SelectTrigger size="xl" className="w-full">
            <SelectValue />
            <SelectIndicator />
          </SelectTrigger>
          <SelectContent className="max-h-72">
            <SelectItem id={ANY_LOCATION}>All locations</SelectItem>
            {locations.map((location) => (
              <SelectItem
                key={location.id}
                id={location.id}
                textValue={location.title}
              >
                {location.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          aria-label="Filter by star rating"
          value={filters.rating === null ? ANY_RATING : String(filters.rating)}
          onChange={(key: string) =>
            onChange({ rating: key === ANY_RATING ? null : Number(key) })
          }
          className="w-full lg:max-w-44"
        >
          <SelectTrigger size="xl" className="w-full">
            <SelectValue />
            <SelectIndicator />
          </SelectTrigger>
          <SelectContent>
            <SelectItem id={ANY_RATING}>Any rating</SelectItem>
            {REVIEW_STAR_RATINGS.map((rating) => (
              <SelectItem
                key={rating}
                id={String(rating)}
                textValue={`${rating} stars`}
              >
                {rating} {rating === 1 ? "star" : "stars"}
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

      {isLocationListPartial ? (
        <p className="text-xs leading-5 text-text-tertiary">
          The location filter lists the first{" "}
          {locations.length.toLocaleString()} locations in this organization.
        </p>
      ) : null}
    </div>
  );
}
