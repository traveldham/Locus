"use client";

import { SparkleFill } from "@tailgrids/icons";

/** Concrete openers, so a first-time reader learns what the agent can actually do. */
const SUGGESTIONS = [
  "How is this profile scoring?",
  "Reply to my unanswered reviews",
  "What should I fix first on this profile?",
  "What has changed here recently?",
];

interface AgentEmptyStateProps {
  /** The chosen location's title. */
  locationTitle: string | null;
  onSuggestion: (content: string) => void;
}

export function AgentEmptyState({
  locationTitle,
  onSuggestion,
}: AgentEmptyStateProps) {
  return (
    <div className="flex flex-col items-start gap-4 py-2">
      <span className="flex size-10 items-center justify-center rounded-full bg-badge-primary-background">
        <SparkleFill
          className="size-5 text-badge-primary-text"
          aria-hidden="true"
        />
      </span>

      <div className="space-y-1">
        <p className="text-sm font-semibold text-text-primary">
          {`Ask about ${locationTitle ?? "this profile"}`}
        </p>
        <p className="text-xs leading-5 text-text-secondary">
          The assistant can audit the profile, read and answer Google reviews,
          and edit profile fields for you. It says what it is about to do before
          it does it.
        </p>
      </div>

      <ul className="flex w-full flex-col gap-2">
        {SUGGESTIONS.map((suggestion) => (
          <li key={suggestion}>
            <button
              type="button"
              onClick={() => onSuggestion(suggestion)}
              className="flex min-h-11 w-full items-center rounded-xl border border-card-border bg-background-gray-secondary px-3.5 py-2.5 text-left text-sm leading-5 text-text-primary transition outline-none hover:border-brand-500 hover:bg-background-gray-tertiary focus-visible:ring-4 focus-visible:ring-button-outline-focus-ring"
            >
              {suggestion}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
