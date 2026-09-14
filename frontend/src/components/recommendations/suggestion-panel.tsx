"use client";

import { reviewErrorMessage } from "@/components/reviews/review-error-message";
import { Badge } from "@/components/tailgrids/core/badge";
import { Button } from "@/components/tailgrids/core/button";
import {
  useApplyLocationEditMutation,
  useAttributeCatalogQuery,
} from "@/hooks/use-locations";
import { auditLatestKey } from "@/hooks/use-recommendations";
import { useReplyToReviewMutation } from "@/hooks/use-reviews";
import { ApiError } from "@/services/api/client";
import type {
  AttributeCatalogItem,
  AttributeInput,
} from "@/services/api/locations";
import type {
  Recommendation,
  Suggestion,
  SuggestionField,
} from "@/services/api/recommendations";
import { SUGGESTION_SHAPE } from "@/services/api/recommendations";
import { REPLY_MAX_LENGTH } from "@/services/api/reviews";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { storeDraft } from "./draft-handoff";

const CONFIDENCE_COLOR = {
  high: "success",
  medium: "blue",
  low: "gray",
} as const;

/**
 * Exhaustive by type, not by habit: five of these were missing while `field` was a
 * `string`, and their headings rendered as raw snake_case with nobody the wiser.
 */
const FIELD_LABEL: Record<SuggestionField, string> = {
  description: "description",
  additional_categories: "additional categories",
  attributes: "attribute answers",
  title: "business name",
  review_reply: "review reply",
  followup_message: "customer follow-up",
  investigation_plan: "investigation plan",
  post_drafts: "post ideas",
  photo_shot_list: "photo checklist",
  themes: "review themes",
  keyword_plan: "keyword plan",
  term_action: "search term action",
  reminder_plan: "reminder plan",
  hours_note: "hours note",
};

/** The heading for a field, staying readable if the API ever names one we do not know. */
function fieldLabel(field: string): string {
  return (
    FIELD_LABEL[field as SuggestionField] ?? field.replaceAll("_", " ").trim()
  );
}

/**
 * A drafted answer to one review. `review_reply` is the only spelling any check declares;
 * the bare `reply` is kept as a runtime alias only, and is not part of `SuggestionField`.
 */
const REPLY_FIELDS = new Set(["review_reply", "reply"]);

/**
 * The review a finding is about, as an id the reviews API will accept.
 *
 * `subject` is Google's review id: stable, and what identifies the finding across audits,
 * but `PUT /reviews/{id}/reply` addresses our own row. The finding's reviews evidence is
 * exactly that one row, so it supplies the id and the subject only decides whether a
 * review is named at all — a finding with no subject is not about a single review.
 */
export function replyTargetId(item: Recommendation): string | null {
  if (!item.subject) return null;
  return (
    item.evidence.find((entry) => entry.source === "reviews")?.row_ids[0] ??
    null
  );
}

/**
 * The draft as it would be published, or "" when this suggestion is not one.
 *
 * Length is part of being sendable, not a separate check: Google refuses a longer reply,
 * so a draft over the cap can only be copied and shortened by hand. Shared with the bulk
 * path so both agree on exactly which drafts a button may publish.
 */
export function replyDraftText(suggestion: Suggestion | null): string {
  if (!suggestion || !REPLY_FIELDS.has(suggestion.field)) return "";
  if (typeof suggestion.value !== "string") return "";
  const draft = suggestion.value.trim();
  return draft.length > 0 && draft.length <= REPLY_MAX_LENGTH ? draft : "";
}

/**
 * A 404 here does not mean what it means in the inbox: an audit is a saved run, so the
 * review it names may simply be gone by the time someone acts on the finding.
 */
export function replySendErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 404) {
    return "This review is no longer in Locus, so nothing was sent. It may have been removed since this audit ran. Your draft is still here.";
  }
  return reviewErrorMessage(error, "reply");
}

/** A JSON object and nothing else: `null` and arrays are objects too. */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Attribute keys are Google's snake_case names; nothing else drafted is. */
function attributeLabel(name: string): string {
  return name.replaceAll("_", " ");
}

/**
 * The draft as plain text, for the clipboard.
 *
 * The field decides how a key/value pair reads — an attribute answer is a question and
 * its yes or no, a keyword plan is a keyword and a sentence of advice about it — but the
 * value that actually arrived decides how it is rendered, so a sentence never becomes
 * "yes" just because a non-empty string is truthy.
 */
function suggestionText(suggestion: Suggestion): string {
  const value = suggestion.value;
  if (typeof value === "string") return value;
  if (Array.isArray(value)) return value.join(", ");
  if (!isRecord(value)) return String(value);
  const shape = SUGGESTION_SHAPE[suggestion.field];
  return Object.entries(value)
    .map(([name, entry]) => {
      const label = shape === "flags" ? attributeLabel(name) : name;
      const text =
        typeof entry === "boolean" ? (entry ? "yes" : "no") : String(entry);
      return `${label}: ${text}`;
    })
    .join("\n");
}

/** The drafted yes/no answers, keeping only the entries that really are answers. */
function attributeAnswers(suggestion: Suggestion): [string, boolean][] {
  if (suggestion.field !== "attributes" || !isRecord(suggestion.value))
    return [];
  return Object.entries(suggestion.value).filter(
    (entry): entry is [string, boolean] => typeof entry[1] === "boolean",
  );
}

/**
 * A yes/no answer travels in Google's `BOOL` container. Any other container takes a very
 * different value, so an attribute the catalog types as something else cannot carry the
 * answer that was drafted for it and is left out rather than reshaped.
 */
const BOOLEAN_VALUE_TYPE = "BOOL";

/** Names are compared as the catalog and the draft both spell them: loosely. */
function attributeKey(name: string): string {
  return name.trim().toLowerCase();
}

/**
 * Drafted answers turned into what `POST /locations/{id}/edits` takes, plus the keys that
 * could not be converted.
 *
 * The identity chain is: the profile stores `attributes/<name>`, the audit strips that
 * prefix to get the drafted key, and the catalog publishes the same `<name>`. So the
 * catalog entry supplies both the type and the canonical spelling of the id — the drafted
 * key is only used to find it. A key with no catalog entry, or one the catalog types as
 * something other than a boolean, is skipped and named: guessing a `value_type` would put
 * a malformed write on a live profile.
 */
export function attributeEdits(
  answers: [string, boolean][],
  catalog: AttributeCatalogItem[] | undefined,
): { edits: AttributeInput[]; skipped: string[] } {
  const byName = new Map<string, AttributeCatalogItem>();
  for (const item of catalog ?? []) {
    byName.set(attributeKey(item.attribute_name), item);
  }
  const edits: AttributeInput[] = [];
  const skipped: string[] = [];
  for (const [name, answer] of answers) {
    const item = byName.get(attributeKey(name));
    if (!item || item.value_type.trim().toUpperCase() !== BOOLEAN_VALUE_TYPE) {
      skipped.push(name);
      continue;
    }
    edits.push({
      attribute_id: `attributes/${item.attribute_name}`,
      value_type: item.value_type,
      values: [answer],
    });
  }
  return { edits, skipped };
}

/** The `field_errors` an edit is rejected with, as one sentence, or "". */
function fieldErrorText(detail: unknown): string {
  if (!isRecord(detail)) return "";
  const errors = detail.field_errors;
  if (!isRecord(errors)) return "";
  return Object.values(errors)
    .filter((message): message is string => typeof message === "string")
    .join(" ")
    .trim();
}

/**
 * Why an attribute update did not land, in the caller's words.
 *
 * A 422 is the profile's contents being refused, and the reason is per field; a 502 is
 * Google refusing the call. Either way nothing on the profile moved and the draft stands.
 */
export function attributeApplyErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 422) {
      const reasons = fieldErrorText(error.detail);
      return reasons
        ? `Google would not accept these answers: ${reasons} Nothing changed on your profile, and the draft is still here.`
        : error.message;
    }
    if (error.status === 502) {
      return "Google rejected this update, so nothing changed on your profile. The draft is still here — try again.";
    }
    return error.message;
  }
  return "The update did not reach Locus. Nothing changed on your profile — check your connection, then try again.";
}

/** Joins names the way a sentence does, so the skipped list reads as prose. */
function nameList(names: string[]): string {
  const labelled = names.map(attributeLabel);
  if (labelled.length <= 1) return labelled.join("");
  return `${labelled.slice(0, -1).join(", ")} and ${labelled[labelled.length - 1]}`;
}

/**
 * Applies drafted attribute answers to the live profile.
 *
 * Its own component so the attribute catalog is only fetched for the drafts that need it,
 * and so the answers above stay on screen while this reports on them.
 */
function ApplyAttributesAction({
  locationId,
  answers,
}: {
  locationId: string;
  answers: [string, boolean][];
}) {
  const client = useQueryClient();
  const catalog = useAttributeCatalogQuery();
  const apply = useApplyLocationEditMutation(locationId);
  /** A request that succeeded but came back as a failed action. */
  const [rejection, setRejection] = useState<ApiError | null>(null);

  const { edits, skipped } = useMemo(
    () => attributeEdits(answers, catalog.data?.items),
    [answers, catalog.data],
  );

  const failure = apply.error ?? rejection;
  const applied = apply.isSuccess && rejection === null;
  const ready = catalog.isSuccess && edits.length > 0;
  // The catalog is in and typed none of these answers: there is nothing to offer.
  const nothingToSend = catalog.isSuccess && edits.length === 0;

  function applyAnswers() {
    if (!ready || apply.isPending || applied) return;
    setRejection(null);
    apply.mutate(
      { attributes: edits },
      {
        // A 201 only records that the attempt was made; the action carries Google's verdict.
        onSuccess: (action) => {
          if (action.status === "failed") {
            setRejection(
              new ApiError(
                action.error ??
                  "Google did not apply these answers. No reason was returned.",
                502,
              ),
            );
            return;
          }
          // The mutation refreshes the profile itself. The audit is a stored run that
          // still reads these attributes as unanswered, so it is refetched too.
          void client.invalidateQueries({
            queryKey: auditLatestKey(locationId),
          });
        },
      },
    );
  }

  return (
    <div className="mt-3 border-t border-card-border pt-3">
      {catalog.isError ? (
        <div>
          <p role="alert" className="text-xs leading-5 text-badge-error-text">
            Locus could not load the attribute list, so it cannot tell how
            Google stores these answers. Nothing was sent.
          </p>
          <Button
            type="button"
            size="xl"
            appearance="outline"
            className="mt-2"
            onPress={() => void catalog.refetch()}
          >
            Try again
          </Button>
        </div>
      ) : (
        <>
          {/* Nothing to press when nothing resolved: the explanation below is the answer. */}
          {nothingToSend ? (
            <p className="text-xs leading-5 text-text-secondary">
              These answers cannot be applied from here. Locus could not confirm
              how Google stores a yes or no for {nameList(skipped)}, and will
              not guess at it. Copy the draft and set{" "}
              {skipped.length === 1 ? "it" : "them"} in the profile editor.
            </p>
          ) : (
            <>
              <div className="flex flex-wrap items-center gap-2">
                <Button
                  type="button"
                  size="xl"
                  onPress={applyAnswers}
                  isDisabled={!ready || apply.isPending || applied}
                >
                  {applied
                    ? "Answers applied"
                    : apply.isPending
                      ? "Applying…"
                      : catalog.isPending
                        ? "Checking attribute types…"
                        : failure
                          ? "Try again"
                          : edits.length === 1
                            ? "Apply this answer to Google"
                            : `Apply these ${edits.length} answers to Google`}
                </Button>
                <span className="text-xs leading-5 text-text-tertiary">
                  {ready
                    ? "Sends only the answers above. Every other attribute on your profile is left as it is."
                    : "Checking how Google stores each of these answers."}
                </span>
              </div>
              {skipped.length > 0 ? (
                <p className="mt-2 text-xs leading-5 text-text-secondary">
                  Leaving out {nameList(skipped)}: Locus could not confirm how
                  Google stores a yes or no for{" "}
                  {skipped.length === 1 ? "it" : "them"}, and will not guess at{" "}
                  {skipped.length === 1 ? "it" : "them"}. Copy the draft and set{" "}
                  {skipped.length === 1 ? "it" : "them"} in the profile editor.
                </p>
              ) : null}
            </>
          )}
          {applied ? (
            <p role="status" className="mt-2 text-xs text-badge-success-text">
              Applied to your Business Profile. This finding still reads as
              unresolved until the next audit runs.
            </p>
          ) : null}
          {failure ? (
            <p
              role="alert"
              className="mt-2 rounded-lg bg-badge-error-background px-3 py-2 text-xs leading-5 text-badge-error-text"
            >
              {attributeApplyErrorMessage(failure)}
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}

/** A generated fix, clearly marked as a draft. Nothing here is published on its own. */
export function SuggestionPanel({
  suggestion,
  locationId,
  reviewId,
}: {
  suggestion: Suggestion;
  locationId: string;
  /** The review this draft answers, when the finding is about exactly one. */
  reviewId?: string | null;
}) {
  const router = useRouter();
  const client = useQueryClient();
  const reply = useReplyToReviewMutation();
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState(false);
  const editable =
    (suggestion.field === "description" || suggestion.field === "title") &&
    typeof suggestion.value === "string";

  // Nothing is offered for an `attributes` draft that carried no real yes/no answers.
  const answers = useMemo(() => attributeAnswers(suggestion), [suggestion]);

  const replyDraft = replyDraftText(suggestion);
  // No button is offered unless it can actually publish: a draft with no review to attach
  // it to, or one Google would refuse for length, is worse than the Copy path alone.
  const sendable =
    reviewId && replyDraft ? { id: reviewId, comment: replyDraft } : null;
  const sent = reply.isSuccess;

  function send() {
    if (!sendable || reply.isPending || sent) return;
    reply.mutate(sendable, {
      // The reviews cache is already refreshed by the mutation. This run is a stored
      // document that keeps calling the review unanswered, but its `inputs_changed`
      // check reads live rows, so refetching it is what surfaces the new state.
      onSuccess: () => {
        void client.invalidateQueries({ queryKey: auditLatestKey(locationId) });
      },
    });
  }

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
      await navigator.clipboard.writeText(suggestionText(suggestion));
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
            · {fieldLabel(suggestion.field)}
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
        <SuggestedValue suggestion={suggestion} />
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
        {sendable ? (
          <Button
            type="button"
            size="xl"
            onPress={send}
            isDisabled={reply.isPending || sent}
          >
            {sent
              ? "Reply sent"
              : reply.isPending
                ? "Sending…"
                : "Send this reply to Google"}
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
            : sendable
              ? "Sends the text above word for word, published publicly on Google under your business name next to this review. Read it first."
              : suggestion.field === "attributes"
                ? "Check each answer against how your business really operates before you apply it."
                : suggestion.field === "additional_categories"
                  ? "Review these categories before adding them to your Business Profile."
                  : "Copy this draft, check it against your business and adapt it before using it."}
        </span>
      </div>
      {answers.length > 0 ? (
        <ApplyAttributesAction locationId={locationId} answers={answers} />
      ) : null}
      {sent ? (
        <p role="status" className="mt-2 text-xs text-badge-success-text">
          Sent. This finding clears on the next audit.
        </p>
      ) : null}
      {reply.isError ? (
        <p
          role="alert"
          className="mt-2 rounded-lg bg-badge-error-background px-3 py-2 text-xs leading-5 text-badge-error-text"
        >
          {replySendErrorMessage(reply.error)}
        </p>
      ) : null}
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

/**
 * The draft, drawn the way its field is shaped.
 *
 * Dispatching on the runtime value alone cannot tell a `Record<string, boolean>` from a
 * `Record<string, string>`, and treating both as answers turned every drafted keyword
 * sentence into the word "Yes". The field decides the layout; the value is still checked
 * before it is used, because a type is a promise about the server, not a guarantee.
 */
function SuggestedValue({ suggestion }: { suggestion: Suggestion }) {
  const shape = SUGGESTION_SHAPE[suggestion.field];
  const value = suggestion.value;

  if (shape === "list" && Array.isArray(value)) {
    return (
      <ul className="list-disc pl-5">
        {value.map((item, index) => (
          <li key={`${index}-${String(item)}`}>{item}</li>
        ))}
      </ul>
    );
  }

  if (shape === "notes" && isRecord(value)) {
    // A subject and the sentence of advice about it: the sentence is the whole point,
    // so it gets its own line rather than a column that would clip it.
    return (
      <dl className="grid gap-y-2">
        {Object.entries(value).map(([subject, note]) => (
          <div key={subject}>
            <dt className="font-medium text-text-primary">{subject}</dt>
            <dd className="mt-0.5 text-text-secondary">{String(note)}</dd>
          </div>
        ))}
      </dl>
    );
  }

  if (shape === "flags" && isRecord(value)) {
    return (
      <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
        {Object.entries(value).map(([name, answer]) => (
          <div key={name} className="flex justify-between gap-3">
            <dt className="text-text-secondary">{attributeLabel(name)}</dt>
            <dd className="font-medium">
              {typeof answer === "boolean"
                ? answer
                  ? "Yes"
                  : "No"
                : String(answer)}
            </dd>
          </div>
        ))}
      </dl>
    );
  }

  // Text, and every pairing the field did not promise. Paragraph breaks are part of a
  // reply that is sent word for word, so they survive.
  return <p className="whitespace-pre-line">{suggestionText(suggestion)}</p>;
}
