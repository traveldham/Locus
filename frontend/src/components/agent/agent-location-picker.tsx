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

interface AgentLocationPickerProps {
  locations: LocationSummary[];
  /** The chosen location's id. */
  value: string | null;
  onChange: (value: string) => void;
  isLoading: boolean;
  /** A list that could not be read, which is not the same as an empty one. */
  error: Error | null;
  onRetry: () => void;
}

/**
 * Which location the widget is talking about, chosen here rather than read from the page.
 * The panel is on every screen, including the ones that name no location at all.
 */
export function AgentLocationPicker({
  locations,
  value,
  onChange,
  isLoading,
  error,
  onRetry,
}: AgentLocationPickerProps) {
  // A failed request is never reported as "you have no locations": that reads as a fact
  // about the account and leaves nothing to act on.
  if (locations.length === 0 && error) {
    return (
      <p className="px-1 text-xs leading-5 text-badge-error-text">
        Your profiles could not be loaded.{" "}
        <button
          type="button"
          onClick={onRetry}
          className="font-semibold underline underline-offset-2 outline-none focus-visible:ring-4 focus-visible:ring-button-outline-focus-ring"
        >
          Try again
        </button>
      </p>
    );
  }

  if (locations.length === 0) {
    return (
      <p className="px-1 text-xs leading-5 text-text-tertiary">
        {isLoading
          ? "Loading your profiles…"
          : "Import a profile to start a conversation."}
      </p>
    );
  }

  const triggerLabel =
    locations.find((location) => location.id === value)?.title ??
    "Choose a profile";

  return (
    <Select
      aria-label="What this conversation is about"
      value={value ?? undefined}
      onChange={(key: string) => onChange(key)}
      className="w-full"
    >
      <SelectTrigger size="md" className="w-full">
        {/* Rendered through SelectValue rather than instead of it, so react-aria's own
            label wiring for the trigger stays intact, and a long title truncates rather
            than widening the trigger past the panel. */}
        <SelectValue>
          {() => <span className="truncate">{triggerLabel}</span>}
        </SelectValue>
        <SelectIndicator />
      </SelectTrigger>
      {/* Above the panel: the popover portals to the body, behind it by default. */}
      <SelectContent className="z-50 max-h-64">
        {locations.map((location) => (
          <SelectItem
            key={location.id}
            id={location.id}
            textValue={location.title}
            className="min-h-11"
          >
            {location.title}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
