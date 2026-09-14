"use client";

import { Spinner } from "@/components/tailgrids/core/spinner";
import type { AgentMessage, TurnResponse } from "@/services/api/agent";
import { cn } from "@/utils/cn";
import { AgentActivity } from "./agent-activity";
import { AgentEmptyState } from "./agent-empty-state";
import { agentErrorMessage } from "./agent-error";
import { AgentMarkdown } from "./agent-markdown";
import { toolLabel } from "./tool-labels";
import { buildTranscript } from "./transcript-blocks";

/**
 * One turn of the conversation.
 *
 * The two roles are rendered by deliberately different rules. What the reader typed is
 * shown exactly as they typed it, newlines and asterisks and all — they did not ask for it
 * to be interpreted. The agent writes markdown, so its side is rendered as rich text,
 * through the one component that knows the text is untrusted.
 */
function Bubble({
  role,
  content,
  isPending,
}: {
  role: "user" | "assistant";
  content: string;
  isPending?: boolean;
}) {
  const isUser = role === "user";
  return (
    <div
      className={cn(
        "w-fit max-w-[88%] rounded-2xl px-3.5 py-2.5 text-sm leading-6 break-words",
        isUser
          ? "ml-auto rounded-br-md bg-button-primary-background whitespace-pre-wrap text-button-primary-text"
          : "mr-auto rounded-bl-md border border-card-border bg-background-gray-secondary text-text-primary",
        isPending && "opacity-70",
      )}
    >
      {isUser ? content : <AgentMarkdown content={content} />}
    </div>
  );
}

function TranscriptSkeleton() {
  return (
    <div className="flex flex-col gap-3" aria-hidden="true">
      <div className="ml-auto h-10 w-40 animate-pulse rounded-2xl bg-background-gray-secondary" />
      <div className="h-16 w-56 animate-pulse rounded-2xl bg-background-gray-secondary" />
      <div className="h-10 w-44 animate-pulse rounded-2xl bg-background-gray-secondary" />
    </div>
  );
}

function Notice({
  title,
  detail,
  onRetry,
}: {
  title: string;
  detail: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="rounded-xl bg-badge-error-background px-3.5 py-3 text-xs leading-5 text-badge-error-text"
    >
      <p className="font-semibold">{title}</p>
      <p className="mt-0.5">{detail}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-1 inline-flex min-h-11 items-center rounded-lg font-semibold underline underline-offset-2 outline-none focus-visible:ring-4 focus-visible:ring-button-outline-focus-ring"
        >
          Try again
        </button>
      ) : null}
    </div>
  );
}

export interface AgentTranscriptProps {
  messages: AgentMessage[];
  /** Shown before the server has written the message the person just sent. */
  pendingMessage: string | null;
  /** The reply as it arrives over the stream, before the server has written it down. */
  streamingText: string | null;
  turn: TurnResponse | null;
  isBusy: boolean;
  isLoading: boolean;
  loadError: Error | null;
  sendError: Error | null;
  /** A poll that gave up while the agent was supposedly still working. */
  pollError: Error | null;
  /** The chosen location's title. */
  locationTitle: string | null;
  onRetryLoad: () => void;
  onSuggestion: (content: string) => void;
}

export function AgentTranscript({
  messages,
  pendingMessage,
  streamingText,
  turn,
  isBusy,
  isLoading,
  loadError,
  sendError,
  pollError,
  locationTitle,
  onRetryLoad,
  onSuggestion,
}: AgentTranscriptProps) {
  const blocks = buildTranscript(messages);
  const isEmpty =
    blocks.length === 0 && !pendingMessage && !streamingText && !isBusy;

  if (isLoading && blocks.length === 0) return <TranscriptSkeleton />;

  if (loadError && blocks.length === 0) {
    return (
      <Notice
        title="This conversation could not be loaded."
        detail={agentErrorMessage(
          loadError,
          "The assistant could not be reached.",
        )}
        onRetry={onRetryLoad}
      />
    );
  }

  if (isEmpty) {
    return (
      <AgentEmptyState
        locationTitle={locationTitle}
        onSuggestion={onSuggestion}
      />
    );
  }

  const activeLabel =
    turn?.status === "running"
      ? toolLabel(turn.current_tool, "active")
      : "Thinking";

  return (
    <div className="flex flex-col gap-3">
      {blocks.map((block) =>
        block.kind === "message" ? (
          <Bubble key={block.id} role={block.role} content={block.content} />
        ) : (
          <AgentActivity key={block.id} items={block.items} />
        ),
      )}

      {pendingMessage ? (
        <Bubble role="user" content={pendingMessage} isPending />
      ) : null}

      {/* The reply being written. Half-formed markdown is expected here and renders as the
          literal characters received so far, which is what a reader watching text arrive
          would expect to see. It is replaced by the persisted row in the same render that
          row arrives, so the bubble is never absent and never blinks. */}
      {streamingText ? (
        <Bubble role="assistant" content={streamingText} />
      ) : null}

      {/* Announced from the panel's permanent live region, not from here. */}
      {isBusy ? (
        <p className="flex items-center gap-2 text-xs leading-5 text-text-secondary">
          <Spinner size="sm" className="size-4 shrink-0" />
          {activeLabel}
          <span aria-hidden="true">…</span>
        </p>
      ) : null}

      {turn?.status === "failed" ? (
        <Notice
          title="The assistant could not finish that."
          detail={
            turn.error ??
            "No reason was given. Sending the message again usually works."
          }
        />
      ) : null}

      {pollError ? (
        <Notice
          title="Lost track of what the assistant is doing."
          detail={`${agentErrorMessage(pollError, "The assistant could not be reached.")} Your message may still be running.`}
          onRetry={onRetryLoad}
        />
      ) : null}

      {sendError ? (
        <Notice
          title="That message was not sent."
          detail={`${agentErrorMessage(sendError, "The assistant could not be reached.")} What you typed is still in the box.`}
        />
      ) : null}
    </div>
  );
}
