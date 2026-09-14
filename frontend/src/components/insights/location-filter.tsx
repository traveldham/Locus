"use client";

import {
  Select,
  SelectContent,
  SelectIndicator,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/tailgrids/core/select";
import type { LocationSummary } from "@/services/api/locations";

const ALL_LOCATIONS = "__all_locations__";

interface LocationFilterProps {
  value: string | null;
  onChange: (locationId: string | null) => void;
  locations: LocationSummary[];
  isLoading: boolean;
  /** Shown in place of "All profiles" where a single profile is required. */
  allLabel?: string;
  className?: string;
}

export function LocationFilter({
  value,
  onChange,
  locations,
  isLoading,
  allLabel = "All profiles",
  className = "w-full lg:max-w-64",
}: LocationFilterProps) {
  return (
    <Select
      aria-label="Filter by profile"
      value={value ?? ALL_LOCATIONS}
      onChange={(key: string) => onChange(key === ALL_LOCATIONS ? null : key)}
      isDisabled={isLoading && locations.length === 0}
      className={className}
    >
      <SelectTrigger size="xl" className="w-full">
        <SelectValue />
        <SelectIndicator />
      </SelectTrigger>
      <SelectContent className="max-h-72">
        <SelectItem id={ALL_LOCATIONS}>{allLabel}</SelectItem>
        {locations.map((location) => (
          <SelectItem key={location.id} id={location.id} textValue={location.title}>
            {location.title}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
