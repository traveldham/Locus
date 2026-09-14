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
import {
  searchIntentLabel,
  type SearchIntent,
  type TrackedKeyword,
} from "@/services/api/market";

const ALL_INTENTS = "__all_intents__";

export function LocationSelect({
  locations,
  value,
  onChange,
  isLoading,
  className,
}: {
  locations: LocationSummary[];
  value: string | null;
  onChange: (locationId: string) => void;
  isLoading: boolean;
  className?: string;
}) {
  return (
    <Select
      aria-label="Profile"
      value={value ?? ""}
      onChange={(key: string) => onChange(key)}
      // Nothing to offer until a location arrives, so the control stays disabled
      // rather than opening an empty menu.
      isDisabled={locations.length === 0}
      placeholder={isLoading ? "Loading profiles…" : "Select a profile"}
      className={className}
    >
      <SelectTrigger size="xl" className="w-full">
        <SelectValue />
        <SelectIndicator />
      </SelectTrigger>
      <SelectContent className="max-h-72">
        {locations.map((location) => (
          <SelectItem key={location.id} id={location.id} textValue={location.title}>
            {location.title}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function IntentSelect({
  intents,
  value,
  onChange,
  className,
}: {
  /** Only the intents present in the keywords the API returned. */
  intents: SearchIntent[];
  value: SearchIntent | null;
  onChange: (intent: SearchIntent | null) => void;
  className?: string;
}) {
  return (
    <Select
      aria-label="Filter by search intent"
      value={value ?? ALL_INTENTS}
      onChange={(key: string) =>
        onChange(key === ALL_INTENTS ? null : (key as SearchIntent))
      }
      isDisabled={intents.length === 0}
      className={className}
    >
      <SelectTrigger size="xl" className="w-full">
        <SelectValue />
        <SelectIndicator />
      </SelectTrigger>
      <SelectContent className="max-h-72">
        <SelectItem id={ALL_INTENTS}>All intents</SelectItem>
        {intents.map((intent) => (
          <SelectItem key={intent} id={intent} textValue={searchIntentLabel(intent)}>
            {searchIntentLabel(intent)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function KeywordSelect({
  keywords,
  value,
  onChange,
  className,
}: {
  keywords: TrackedKeyword[];
  value: string | null;
  onChange: (keywordId: string) => void;
  className?: string;
}) {
  return (
    <Select
      aria-label="Tracked keyword"
      value={value ?? ""}
      onChange={(key: string) => onChange(key)}
      isDisabled={keywords.length === 0}
      placeholder="Select a keyword"
      className={className}
    >
      <SelectTrigger size="xl" className="w-full">
        <SelectValue />
        <SelectIndicator />
      </SelectTrigger>
      <SelectContent className="max-h-72">
        {keywords.map((keyword) => (
          <SelectItem key={keyword.id} id={keyword.id} textValue={keyword.keyword}>
            {keyword.keyword}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function WeekSelect({
  weeks,
  value,
  onChange,
  formatLabel,
  className,
}: {
  weeks: string[];
  value: string | null;
  onChange: (weekStart: string) => void;
  formatLabel: (weekStart: string) => string;
  className?: string;
}) {
  return (
    <Select
      aria-label="Week"
      value={value ?? ""}
      onChange={(key: string) => onChange(key)}
      isDisabled={weeks.length === 0}
      placeholder="Select a week"
      className={className}
    >
      <SelectTrigger size="xl" className="w-full">
        <SelectValue />
        <SelectIndicator />
      </SelectTrigger>
      <SelectContent className="max-h-72">
        {weeks.map((week) => (
          <SelectItem key={week} id={week} textValue={`Week of ${formatLabel(week)}`}>
            Week of {formatLabel(week)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
