"use client";

import { AGENT_MESSAGE_MAX_LENGTH } from "@/services/api/agent";
import { cn } from "@/utils/cn";
import { Send1 } from "@tailgrids/icons";
import {
  useState,
  type FormEvent,
  type KeyboardEvent,
  type RefObject,
} from "react";

export interface AgentComposerProps {
  /** Resolves true only when the server has the message. */
  onSend: (content: string) => Promise<boolean>;
  /** Blocked while a turn runs: the agent answers one message at a time. */
  isBusy: boolean;
  isDisabled: boolean;
  placeholder: string;
  inputRef: RefObject<HTMLTextAreaElement | null>;
}

export function AgentComposer({
  onSend,
  isBusy,
  isDisabled,
  placeholder,
  inputRef,
}: AgentComposerProps) {
  const [draft, setDraft] = useState("");
  // Covers the request itself. `isBusy` only turns true once the server has answered, and
  // a second Enter in that window would send the same message twice.
  const [isSubmitting, setIsSubmitting] = useState(false);
  const trimmed = draft.trim();
  const canSend = trimmed.length > 0 && !isBusy && !isDisabled && !isSubmitting;

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!canSend) return;
    setIsSubmitting(true);
    try {
      // Cleared only once the send has actually landed. A message lost to a failed
      // request cannot be recovered, so the text stays put and can be sent again.
      if (await onSend(trimmed)) setDraft("");
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends, Shift+Enter adds a line. IME composition must never send.
    if (
      event.key !== "Enter" ||
      event.shiftKey ||
      event.nativeEvent.isComposing
    ) {
      return;
    }
    event.preventDefault();
    void submit();
  }

  return (
    <form
      onSubmit={submit}
      className="flex items-end gap-2 border-t border-card-border bg-card-surface-area px-3 py-3"
    >
      <label htmlFor="agent-composer" className="sr-only">
        Message the assistant
      </label>
      <textarea
        id="agent-composer"
        ref={inputRef}
        rows={1}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={handleKeyDown}
        // The agent answers one message at a time; the panel refocuses this when the
        // turn releases it.
        disabled={isDisabled || isBusy || isSubmitting}
        maxLength={AGENT_MESSAGE_MAX_LENGTH}
        placeholder={placeholder}
        className="scrollbar-thin max-h-32 min-h-11 w-full resize-none rounded-xl border border-card-border bg-input-background px-3.5 py-2.5 text-sm leading-6 text-text-primary outline-none field-sizing-content placeholder:text-input-placeholder-text focus:border-input-primary-focus-border focus:ring-4 focus:ring-input-primary-focus-border/20 disabled:cursor-not-allowed disabled:bg-input-disabled-background disabled:text-input-disabled-text"
      />
      <button
        type="submit"
        disabled={!canSend}
        aria-label="Send message"
        className={cn(
          "flex size-11 shrink-0 items-center justify-center rounded-xl transition outline-none focus-visible:ring-4 focus-visible:ring-button-primary-focus-ring",
          canSend
            ? "bg-button-primary-background text-button-primary-text hover:bg-button-primary-hover-background"
            : "cursor-not-allowed bg-button-disabled-background text-button-disabled-text",
        )}
      >
        <Send1 className="size-5" aria-hidden="true" />
      </button>
    </form>
  );
}
