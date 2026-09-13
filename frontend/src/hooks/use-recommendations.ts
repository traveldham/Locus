"use client";

import { recommendationApi } from "@/services/api/recommendations";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

const latestKey = (locationId: string) => [
  "recommendations",
  "latest",
  locationId,
];
const DIRECTORY_KEY = ["recommendations", "overview"] as const;
const directoryKey = (projectId: string | null) => [
  ...DIRECTORY_KEY,
  projectId,
];

/** Every profile in the active project, with its own audit. */
export function useAuditDirectory(projectId: string | null) {
  return useQuery({
    queryKey: directoryKey(projectId),
    queryFn: () => recommendationApi.overview(projectId),
    staleTime: 10_000,
    // Cheap: it reads saved audits, no snapshot scan. Keeps running jobs visible.
    refetchInterval: 15_000,
    retry: 1,
  });
}

export function useLatestRecommendations(locationId: string) {
  return useQuery({
    queryKey: latestKey(locationId),
    queryFn: () => recommendationApi.latest(locationId),
    enabled: Boolean(locationId),
    staleTime: 30_000,
    // Each call re-reads every analytical row to fingerprint the inputs, so this is a
    // slow background check for "your data changed", not a live feed. A finishing audit
    // refreshes it directly; it does not need a fast poll.
    refetchInterval: 5 * 60_000,
    refetchOnWindowFocus: false,
    retry: 1,
  });
}

export function useGenerateRecommendations() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: recommendationApi.generate,
    // Queuing changes nothing on screen yet; the job poll publishes the result.
    onSuccess: (job) => {
      void client.invalidateQueries({ queryKey: latestKey(job.location_id) });
      void client.invalidateQueries({ queryKey: DIRECTORY_KEY });
    },
  });
}

/** Polls one audit job while it works, then refreshes the audit once it lands. */
export function useAuditJob(jobId: string | null) {
  const client = useQueryClient();
  const published = useRef<string | null>(null);

  const query = useQuery({
    queryKey: ["recommendations", "job", jobId],
    queryFn: () => recommendationApi.job(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      return status === "pending" || status === "running" ? 2000 : false;
    },
    staleTime: 0,
    retry: 1,
  });

  const status = query.data?.status;
  useEffect(() => {
    // Refreshing from inside the query function would invalidate this very query and
    // loop forever, so publish here instead, once per job, and never touch the job key.
    if (!jobId || (status !== "succeeded" && status !== "failed")) return;
    if (published.current === jobId) return;
    published.current = jobId;
    const locationId = query.data?.location_id;
    if (locationId)
      void client.invalidateQueries({ queryKey: latestKey(locationId) });
    void client.invalidateQueries({ queryKey: DIRECTORY_KEY });
  }, [client, jobId, status, query.data?.location_id]);

  return query;
}
