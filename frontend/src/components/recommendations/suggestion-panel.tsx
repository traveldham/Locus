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
  description: "description",
  additional_categories: "additional categories",
  attributes: "attribute answers",
  title: "business name",
  review_reply: "review reply",
  reply: "review reply",
  followup_message: "customer follow-up",
  investigation_plan: "investigation plan",
  post_drafts: "post ideas",
  photo_shot_list: "photo checklist",
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

/** A generated fix, clearly marked as a draft. Nothing here is published on its own. */
export function SuggestionPanel({
  suggestion,
  locationId,
}: {
  suggestion: Suggestion;
  locationId: string;
}) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
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
      setCopyError(false);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
      setCopyError(true);
    }
  }

  return (
    <section
      aria-label="Suggested fix"
      className="rounded-xl bg-background-gray-secondary px-4 py-4 text-sm"
    >
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="font-medium text-text-primary">
          Suggested fix
          <span className="ml-1.5 font-normal text-text-tertiary">
            ·{" "}
            {FIELD_LABEL[suggestion.field] ??
              suggestion.field.replaceAll("_", " ")}
          </span>
        </h3>
        <Badge color={CONFIDENCE_COLOR[suggestion.confidence]} size="sm">
          {suggestion.confidence} confidence
        </Badge>
        <span className="ml-auto text-xs text-text-tertiary">
          AI draft · review before using
        </span>
      </div>
      <div className="mt-2 leading-6 text-text-primary">
        <SuggestedValue value={suggestion.value} />
      </div>
      <div className="mt-3 border-t border-card-border pt-3">
        <p className="text-xs font-medium text-text-primary">
          Why this draft fits
        </p>
        <p className="mt-1 text-xs leading-5 text-text-secondary">
          {suggestion.reason}
        </p>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        {editable ? (
          <Button type="button" size="xl" onPress={useDraft}>
            Use this draft in the editor
          </Button>
        ) : null}
        <Button
          type="button"
          size="xl"
          appearance="outline"
          onPress={() => void copy()}
        >
          {copied ? "Copied" : "Copy"}
        </Button>
        <span className="text-xs leading-5 text-text-tertiary">
          {editable
            ? "Opens the profile editor prefilled. You still preview and approve before anything is published."
            : suggestion.field === "attributes" ||
                suggestion.field === "additional_categories"
              ? "Review these answers before updating your Business Profile."
              : "Copy this draft, check it against your business and adapt it before using it."}
        </span>
      </div>
      {copied ? (
        <p role="status" className="mt-2 text-xs text-badge-success-text">
          Draft copied to clipboard.
        </p>
      ) : null}
      {copyError ? (
        <p role="alert" className="mt-2 text-xs text-badge-error-text">
          Copy did not work. Select the draft text and copy it manually.
        </p>
      ) : null}
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
