"use client";

import {
  Alert,
  AlertContent,
  AlertDescription,
  AlertIndicator,
  AlertTitle,
} from "@/components/tailgrids/core/alert";
import { Button } from "@/components/tailgrids/core/button";
import { cn } from "@/utils/cn";
import { useSyncExternalStore } from "react";

const STORAGE_KEY = "locus:sample-data-notice-dismissed";

const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function readDismissed() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    // A browser that refuses storage still gets to see the notice.
    return false;
  }
}

function dismiss() {
  try {
    window.localStorage.setItem(STORAGE_KEY, "true");
  } catch {
    // Nothing to persist to; the listeners below still hide it for this visit.
  }
  for (const listener of listeners) listener();
}

/**
 * Says where the locations on this screen came from.
 *
 * Sample locations appearing under someone's real Google account is exactly how a
 * previous build got read as the product inventing data about their business. The chips
 * label each row; this states the reason once, plainly, and stays dismissed per browser.
 */
export function SampleDataNotice({ className }: { className?: string }) {
  // localStorage is read as an external store, and treated as dismissed on the server so
  // the notice never flashes in for someone who already closed it.
  const isDismissed = useSyncExternalStore(subscribe, readDismissed, () => true);

  if (isDismissed) return null;

  return (
    <Alert status="info" className={cn("max-w-none", className)}>
      <AlertIndicator />
      <AlertContent>
        <AlertTitle>These profiles are sample data</AlertTitle>
        <AlertDescription>
          Google has not yet approved this project for Business Profile API access, so the
          profiles below come from a sample dataset instead of your Google account. They are
          marked “Sample data” wherever they appear. Once access is approved, the same screens
          show the real profiles your Google account manages.
        </AlertDescription>
        <Button type="button" size="xl" appearance="outline" onPress={dismiss}>
          Dismiss
        </Button>
      </AlertContent>
    </Alert>
  );
}
