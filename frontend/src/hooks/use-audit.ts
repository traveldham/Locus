"use client";

import { useState } from "react";
import { useAuditJob, useLatestRecommendations } from "./use-recommendations";

/** One profile's current audit, plus any job working on its next one. */
export function useAuditRun(locationId: string) {
  const latest = useLatestRecommendations(locationId);
  // A job the server still reports as running survives a reload; a job this tab just
  // queued is known before the next poll. Either drives the live status.
  const [queuedJobId, setQueuedJobId] = useState<string | null>(null);
  const serverJobId = latest.data?.job?.id ?? null;
  const job = useAuditJob(serverJobId ?? queuedJobId);
  const activeJob = job.data ?? latest.data?.job ?? null;
  return {
    run: latest.data?.run,
    benchmark: latest.data?.benchmark,
    job: activeJob,
    isAuditing:
      activeJob?.status === "pending" || activeJob?.status === "running",
    trackJob: setQueuedJobId,
    inputsChanged: Boolean(latest.data?.inputs_changed),
    isPending: latest.isPending,
    error: latest.error,
    refetch: () => void latest.refetch(),
  };
}
