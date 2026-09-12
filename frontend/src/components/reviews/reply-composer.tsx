"use client";

import { Button } from "@/components/tailgrids/core/button";
import { FieldLabel } from "@/components/tailgrids/core/field";
import { TextArea } from "@/components/tailgrids/core/text-area";
import { TextField } from "@/components/tailgrids/core/text-field";
import { useReplyToReviewMutation } from "@/hooks/use-reviews";
import { REPLY_MAX_LENGTH, type Review } from "@/services/api/reviews";
import { cn } from "@/utils/cn";
import { useState, type FormEvent, type KeyboardEvent } from "react";
import { reviewErrorMessage } from "./review-error-message";

/** Warn while there is still room to edit rather than at the moment typing stops. */
const COUNTER_WARNING_THRESHOLD = REPLY_MAX_LENGTH - 200;

export interface ReplyComposerProps {
  review: Review;
  onClose: () => void;
  className?: string;
}

/**
 * Expands in place under the review so the reviewer's words stay on screen while
 * the reply is written. A failed send never clears the draft.
 */
export function ReplyComposer({ review, onClose, className }: ReplyComposerProps) {
  const isEditing = review.has_reply;
  const [draft, setDraft] = useState(review.reply_comment ?? "");
  const [showEmptyError, setShowEmptyError] = useState(false);
  const reply = useReplyToReviewMutation();

  const trimmed = draft.trim();
  const isEmpty = trimmed.length === 0;
  const isUnchanged = isEditing && trimmed === (review.reply_comment ?? "").trim();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (reply.isPending) return;
    if (isEmpty) {
      setShowEmptyError(true);
      return;
    }
    setShowEmptyError(false);
    reply.mutate({ id: review.id, comment: trimmed }, { onSuccess: onClose });
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        "rounded-lg border border-card-border bg-background-gray-secondary p-4",
        className,
      )}
    >
      <TextField
        value={draft}
        onChange={(value) => {
          setDraft(value);
          if (showEmptyError) setShowEmptyError(false);
        }}
        invalid={showEmptyError}
        disabled={reply.isPending}
        className="gap-1.5"
      >
        <FieldLabel className="cursor-default">
          {isEditing ? "Edit your public reply" : "Write a public reply"}
        </FieldLabel>
        <TextArea
          autoFocus
          rows={4}
          maxLength={REPLY_MAX_LENGTH}
          onKeyDown={handleKeyDown}
          placeholder="Thank the reviewer, answer what they raised, and keep it in your business voice."
          className="w-full text-sm leading-6"
        />
      </TextField>

      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <p className="max-w-md text-xs leading-5 text-text-tertiary">
          Published publicly on Google under your business name, next to this review. Anyone
          who reads the review can read your reply.
        </p>
        <p
          aria-live="polite"
          className={cn(
            "text-xs tabular-nums",
            draft.length >= COUNTER_WARNING_THRESHOLD
              ? "font-medium text-badge-warning-text"
              : "text-text-tertiary",
          )}
        >
          <span className="sr-only">Characters used: </span>
          {draft.length.toLocaleString()} / {REPLY_MAX_LENGTH.toLocaleString()}
        </p>
      </div>

      {showEmptyError ? (
        <p role="alert" className="mt-3 text-sm text-input-error">
          Write a reply before publishing it. A reply of only spaces cannot be sent.
        </p>
      ) : null}

      {reply.isError ? (
        <p
          role="alert"
          className="mt-3 rounded-lg bg-badge-error-background px-3 py-2 text-sm leading-5 text-badge-error-text"
        >
          {reviewErrorMessage(reply.error, "reply")}
        </p>
      ) : null}

      <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:items-center">
        <Button type="submit" size="xl" isDisabled={reply.isPending || isUnchanged}>
          {reply.isPending
            ? "Publishing…"
            : isEditing
              ? "Update public reply"
              : "Publish reply to Google"}
        </Button>
        <Button
          type="button"
          size="xl"
          variant="primary"
          appearance="outline"
          onPress={onClose}
          isDisabled={reply.isPending}
        >
          Cancel
        </Button>
      </div>
    </form>
  );
}
