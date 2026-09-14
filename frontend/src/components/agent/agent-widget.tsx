"use client";

import { useActiveProjectId } from "@/contexts/active-project";
import {
  useAgentChat,
  useAgentLocationChoice,
  useAgentLocationsQuery,
} from "@/hooks/use-agent-chat";
import { cn } from "@/utils/cn";
import { Close, SparkleFill } from "@tailgrids/icons";
import { useEffect, useRef, useState } from "react";
import { AgentPanel } from "./agent-panel";

/**
 * The assistant, as a fixed floating widget rather than a page.
 *
 * Mounted once above the scrolling region, so it is on every authenticated screen, stays
 * put while the page scrolls, and keeps its conversation across navigations. It reads no
 * route, only the active project - the same scope the rest of the dashboard is under - and
 * which of that project's locations to talk about is chosen inside the panel.
 *
 * Data work starts on the first open and keeps running while the panel is collapsed, so a
 * long turn finishes whether or not the reader is watching.
 */
export function AgentWidget() {
  const [isOpen, setIsOpen] = useState(false);
  // The panel is mounted from the first open onwards; before that it costs nothing.
  const [hasOpened, setHasOpened] = useState(false);
  const launcherRef = useRef<HTMLButtonElement>(null);

  const projectId = useActiveProjectId();
  const locationsQuery = useAgentLocationsQuery(projectId, hasOpened);
  const locations = locationsQuery.data ?? [];
  const locationChoice = useAgentLocationChoice(locations);
  const chat = useAgentChat({
    locationId: locationChoice.locationId,
    enabled: hasOpened,
    isPanelOpen: isOpen,
  });

  function open() {
    setHasOpened(true);
    setIsOpen(true);
  }

  function close() {
    setIsOpen(false);
    launcherRef.current?.focus();
  }

  useEffect(() => {
    if (!isOpen) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setIsOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen]);

  return (
    <>
      {hasOpened ? (
        <AgentPanel
          isOpen={isOpen}
          onClose={close}
          locations={locations}
          isLoadingLocations={locationsQuery.isLoading}
          locationsError={locationsQuery.error}
          onRetryLocations={() => void locationsQuery.refetch()}
          locationId={locationChoice.locationId}
          onLocationChange={locationChoice.setValue}
          locationTitle={locationChoice.location?.title ?? null}
          chat={chat}
        />
      ) : null}

      <button
        ref={launcherRef}
        type="button"
        onClick={() => (isOpen ? close() : open())}
        aria-expanded={isOpen}
        aria-label={isOpen ? "Close the assistant" : "Open the assistant"}
        className="fixed right-4 bottom-4 z-40 flex size-14 items-center justify-center rounded-full bg-button-primary-background text-button-primary-text shadow-lg transition outline-none hover:bg-button-primary-hover-background focus-visible:ring-4 focus-visible:ring-button-primary-focus-ring motion-reduce:transition-none sm:right-5 sm:bottom-5"
      >
        {/* Both icons stay mounted and cross-fade, so the button never resizes. */}
        <span className="relative flex size-6 items-center justify-center">
          <SparkleFill
            aria-hidden="true"
            className={cn(
              "absolute size-6 transition duration-200 motion-reduce:transition-none",
              isOpen ? "scale-75 opacity-0" : "scale-100 opacity-100",
            )}
          />
          <Close
            aria-hidden="true"
            className={cn(
              "absolute size-6 transition duration-200 motion-reduce:transition-none",
              isOpen ? "scale-100 opacity-100" : "scale-75 opacity-0",
            )}
          />
        </span>

        {/* A turn that is still running while the panel is collapsed. */}
        {chat.isBusy && !isOpen ? (
          <span className="absolute top-0.5 right-0.5 flex size-3">
            <span className="absolute inline-flex size-3 animate-ping rounded-full bg-badge-success-text opacity-75" />
            <span className="relative inline-flex size-3 rounded-full border-2 border-button-primary-background bg-badge-success-text" />
            <span className="sr-only">The assistant is still working</span>
          </span>
        ) : null}
      </button>
    </>
  );
}
