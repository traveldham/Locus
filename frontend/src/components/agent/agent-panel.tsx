"use client";

import type { AgentChat } from "@/hooks/use-agent-chat";
import type { LocationSummary } from "@/services/api/locations";
import { cn } from "@/utils/cn";
import { Close, Plus, SparkleFill } from "@tailgrids/icons";
import { useEffect, useRef } from "react";
import { AgentComposer } from "./agent-composer";
import { AgentLocationPicker } from "./agent-location-picker";
import { AgentTranscript } from "./agent-transcript";
import { toolLabel } from "./tool-labels";

/** Anything closer than this to the bottom counts as "following the conversation". */
const FOLLOW_THRESHOLD_PX = 80;

export interface AgentPanelProps {
  isOpen: boolean;
  onClose: () => void;
  locations: LocationSummary[];
  isLoadingLocations: boolean;
  locationsError: Error | null;
  onRetryLocations: () => void;
  /** The picker's value: the chosen location's id. */
  locationId: string | null;
  onLocationChange: (value: string) => void;
  /** The chosen location's title. */
  locationTitle: string | null;
  chat: AgentChat;
}

export function AgentPanel({
  isOpen,
  onClose,
  locations,
  isLoadingLocations,
  locationsError,
  onRetryLocations,
  locationId,
  onLocationChange,
  locationTitle,
  chat,
}: AgentPanelProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  // Someone who has scrolled up to re-read something is not dragged back down.
  const isFollowing = useRef(true);

  const { messages, pendingMessage, streamingText, turn, isBusy } = chat;
  // One value that changes whenever the transcript gains something worth seeing. The
  // streamed reply is counted by length rather than carried whole: it changes on every
  // token, which is exactly the cadence the view should follow it at, and the text itself
  // would make this string as long as the answer.
  const scrollSignal = `${messages.length}|${pendingMessage ?? ""}|${streamingText?.length ?? 0}|${turn?.status ?? ""}|${turn?.current_tool ?? ""}|${isBusy}`;

  useEffect(() => {
    if (!isOpen) return;
    inputRef.current?.focus();
  }, [isOpen]);

  // When a turn releases the composer, take focus back only if disabling it is what
  // dropped focus to nowhere. Never steal it from the picker, a chip, or whatever the
  // reader moved to while waiting.
  useEffect(() => {
    if (!isOpen || isBusy) return;
    const active = document.activeElement;
    if (active && active !== document.body) return;
    inputRef.current?.focus();
  }, [isOpen, isBusy]);

  // Another location is another conversation: start following it again, however far up the
  // reader had scrolled in the last one.
  useEffect(() => {
    isFollowing.current = true;
  }, [locationId]);

  useEffect(() => {
    const element = scrollRef.current;
    if (!element || !isOpen || !isFollowing.current) return;
    element.scrollTop = element.scrollHeight;
  }, [isOpen, scrollSignal, locationId]);

  // Mounted whether or not anything is happening: a live region that appears only when it
  // has something to say is announced unreliably.
  const spokenStatus = isBusy
    ? `${turn?.status === "running" ? toolLabel(turn.current_tool, "active") : "Thinking"}…`
    : turn?.status === "failed"
      ? "The assistant could not finish that."
      : "";

  return (
    <section
      role="dialog"
      aria-label="Locus assistant"
      inert={isOpen ? undefined : true}
      onKeyDown={(event) => {
        if (event.key === "Escape") onClose();
      }}
      className={cn(
        "fixed inset-x-4 bottom-20 z-40 flex flex-col overflow-hidden rounded-2xl border border-card-surface-border bg-card-surface-area shadow-2xl",
        "h-[min(30rem,calc(100dvh-7rem))] sm:inset-x-auto sm:right-5 sm:bottom-22 sm:h-[min(38rem,calc(100dvh-7.5rem))] sm:w-104",
        "origin-bottom-right transition duration-200 ease-out motion-reduce:transition-none",
        isOpen
          ? "translate-y-0 scale-100 opacity-100"
          : "pointer-events-none translate-y-3 scale-95 opacity-0",
      )}
    >
      <header className="shrink-0 border-b border-card-border px-3 py-3">
        <div className="flex items-center gap-2.5">
          <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-badge-primary-background">
            <SparkleFill
              className="size-4 text-badge-primary-text"
              aria-hidden="true"
            />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-text-primary">
              Assistant
            </p>
            <p className="truncate text-xs leading-4 text-text-tertiary">
              Audits, reviews and profile edits
            </p>
          </div>
          {/* The way out of a run that never settles, and of a conversation gone wrong.
              Deliberately available while the agent is busy: that is when it is needed. */}
          <button
            type="button"
            onClick={chat.startNewChat}
            disabled={!chat.canStartNewChat}
            title="Start a new chat"
            aria-label="Start a new chat"
            className="flex size-11 shrink-0 items-center justify-center rounded-lg text-icon-secondary transition outline-none hover:bg-button-primary-outline-hover-background hover:text-text-primary focus-visible:ring-4 focus-visible:ring-button-outline-focus-ring disabled:pointer-events-none disabled:opacity-40"
          >
            <Plus className="size-5" aria-hidden="true" />
          </button>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close the assistant"
            className="flex size-11 shrink-0 items-center justify-center rounded-lg text-icon-secondary transition outline-none hover:bg-button-primary-outline-hover-background hover:text-text-primary focus-visible:ring-4 focus-visible:ring-button-outline-focus-ring"
          >
            <Close className="size-5" aria-hidden="true" />
          </button>
        </div>

        <div className="mt-2.5">
          <AgentLocationPicker
            locations={locations}
            value={locationId}
            onChange={onLocationChange}
            isLoading={isLoadingLocations}
            error={locationsError}
            onRetry={onRetryLocations}
          />
        </div>
      </header>

      <div
        ref={scrollRef}
        onScroll={(event) => {
          const element = event.currentTarget;
          isFollowing.current =
            element.scrollHeight - element.scrollTop - element.clientHeight <
            FOLLOW_THRESHOLD_PX;
        }}
        className="scrollbar-thin min-h-0 flex-1 overflow-y-auto px-3.5 py-4"
      >
        {locationId ? (
          <AgentTranscript
            messages={messages}
            pendingMessage={pendingMessage}
            streamingText={streamingText}
            turn={turn}
            isBusy={isBusy}
            isLoading={chat.isLoading}
            loadError={chat.loadError}
            sendError={chat.sendError}
            pollError={chat.pollError}
            locationTitle={locationTitle}
            onRetryLoad={chat.retryLoad}
            onSuggestion={(content) => void chat.send(content)}
          />
        ) : (
          <p className="text-sm leading-6 text-text-secondary">
            {isLoadingLocations
              ? "Loading your profiles…"
              : locationsError
                ? "Your profiles could not be loaded, so there is nothing to talk about yet."
                : "Connect a Google Business Profile first. You can then ask the assistant about it."}
          </p>
        )}
      </div>

      <p className="sr-only" aria-live="polite">
        {spokenStatus}
      </p>

      <AgentComposer
        inputRef={inputRef}
        onSend={chat.send}
        isBusy={isBusy}
        // Sending before the conversation list has answered would start a second
        // conversation and strand the first, which nothing in the widget can reach again.
        isDisabled={!locationId || !chat.isReady}
        placeholder={
          !locationId
            ? "Choose a profile first…"
            : !chat.isReady
              ? chat.loadError
                ? "Reconnect to send a message…"
                : "Opening your conversation…"
              : isBusy
                ? "Working on your last message…"
                : "Ask about this profile…"
        }
      />
    </section>
  );
}
