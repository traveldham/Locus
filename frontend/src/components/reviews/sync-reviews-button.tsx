"use client";

import { Button } from "@/components/tailgrids/core/button";
import { RefreshCircle3Clockwise } from "@tailgrids/icons";

export interface SyncReviewsButtonProps {
  onSync: () => void;
  isSyncing: boolean;
  appearance?: "fill" | "outline";
}

export function SyncReviewsButton({
  onSync,
  isSyncing,
  appearance = "outline",
}: SyncReviewsButtonProps) {
  return (
    <Button size="xl" appearance={appearance} onPress={onSync} isDisabled={isSyncing}>
      <RefreshCircle3Clockwise
        aria-hidden="true"
        focusable="false"
        className="size-4 shrink-0"
      />
      {isSyncing ? "Syncing…" : "Sync reviews"}
    </Button>
  );
}
