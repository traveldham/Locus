"use client";

import { Badge } from "@/components/tailgrids/core/badge";
import { Button } from "@/components/tailgrids/core/button";
import type { Suggestion } from "@/services/api/recommendations";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { storeDraft } from "./draft-handoff";

const CONFIDENCE_COLOR = {
  high: "success",
  medium: "blue",
  low: "gray",
} as const;

const FIELD_LABEL: Record<string, string> = {
  description: "Suggested description",
  additional_categories: "Suggested additional categories",
  attributes: "Suggested attribute answers",
  title: "Suggested name",
};

function asText(value: Suggestion["value"]): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.join(", ");
  return Object.entries(value)
    .map(
      ([name, answer]) =>
        `${name.replaceAll("_", " ")}: ${answer ? "yes" : "no"}`,
    )
    .join("\n");
}

/** A generated draft, clearly marked as such. Nothing here is published on its own. */
export function SuggestionPanel({
  suggestion,
  locationId,
}: {
  suggestion: Suggestion;
  locationId: string;
}) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const editable =
    (suggestion.field === "description" || suggestion.field === "title") &&
    typeof suggestion.value === "string";

  function useDraft() {
    if (!editable || typeof suggestion.value !== "string") return;
    storeDraft(locationId, {
      field: suggestion.field as "title" | "description",
      value: suggestion.value,
      reason: suggestion.reason,
    });
    router.push(`/locations/${encodeURIComponent(locationId)}?draft=1`);
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(asText(suggestion.value));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <section
      aria-label="Suggested draft"
      className="mt-4 rounded-lg border border-primary-500/30 bg-card-background px-4 py-3 text-sm"
    >
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-medium text-text-primary">
          {FIELD_LABEL[suggestion.field] ?? `Suggested ${suggestion.field}`}
        </h3>
        <Badge color={CONFIDENCE_COLOR[suggestion.confidence]} size="sm">
          {suggestion.confidence} confidence
        </Badge>
        <span className="ml-auto text-xs text-text-tertiary">
          Drafted by {suggestion.model}
        </span>
      </div>
      <div className="mt-2 leading-6 text-text-primary">
        <SuggestedValue value={suggestion.value} />
      </div>
      <p className="mt-2 text-xs leading-5 text-text-secondary">
        {suggestion.reason}
      </p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {editable ? (
          <Button type="button" size="sm" onPress={useDraft}>
            Use this draft in the editor
          </Button>
        ) : null}
        <Button
          type="button"
          size="sm"
          appearance="outline"
          onPress={() => void copy()}
        >
          {copied ? "Copied" : "Copy"}
        </Button>
        <span className="text-xs leading-5 text-text-tertiary">
          {editable
            ? "Opens the profile editor prefilled. You still preview and approve before anything is published."
            : "Categories and attributes are set in the Business Profile; copy the answers to take with you."}
        </span>
      </div>
    </section>
  );
}

function SuggestedValue({ value }: { value: Suggestion["value"] }) {
  if (typeof value === "string") return <p>{value}</p>;
  if (Array.isArray(value)) {
    return (
      <ul className="list-disc pl-5">
        {value.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    );
  }
  return (
    <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
      {Object.entries(value).map(([name, answer]) => (
        <div key={name} className="flex justify-between gap-3">
          <dt className="text-text-secondary">{name.replaceAll("_", " ")}</dt>
          <dd className="font-medium">{answer ? "Yes" : "No"}</dd>
        </div>
      ))}
    </dl>
  );
}
