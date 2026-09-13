"use client";

import type { AuditJob } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";

/** Live status of a queued audit. The audit already on screen stays readable. */
export function AuditProgress({
  job,
  hasPrevious = true,
}: {
  job: AuditJob | null;
  /** False before a profile's first audit, when there is nothing to keep reading. */
  hasPrevious?: boolean;
}) {
  if (!job) return null;

  if (job.status === "failed") {
    return (
      <div
        role="alert"
        className="mt-4 rounded-lg border border-card-border bg-badge-error-background px-4 py-3 text-sm text-badge-error-text"
      >
        <p className="font-medium">This audit did not finish.</p>
        <p className="mt-1 leading-6">
          {job.error ?? "The worker stopped without recording a reason."} The
          audit below is the last one that completed.
        </p>
      </div>
    );
  }

  if (job.status === "succeeded") return null;

  const queued = job.status === "pending";
  return (
    <div
      role="status"
      aria-live="polite"
      className="mt-4 rounded-lg border border-card-border bg-card-background px-4 py-3"
    >
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span
          className="size-2 shrink-0 animate-pulse rounded-full bg-primary-500"
          aria-hidden="true"
        />
        <span className="font-medium text-text-primary">
          {queued ? "Audit queued" : job.stage}
        </span>
        <span className="text-text-tertiary">
          {queued
            ? "Waiting for a worker to pick it up."
            : `Running in the background · ${job.progress}%`}
        </span>
        {hasPrevious ? (
          <span className="ml-auto text-xs text-text-tertiary">
            You can keep reading the previous audit below.
          </span>
        ) : null}
      </div>
      <div
        className="mt-2.5 h-1.5 w-full overflow-hidden rounded-full bg-background-gray-secondary"
        role="progressbar"
        aria-valuenow={job.progress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Audit progress"
      >
        <div
          className={cn(
            "h-full rounded-full bg-primary-500 transition-[width] duration-500",
            queued && "animate-pulse",
          )}
          style={{ width: `${Math.max(job.progress, 4)}%` }}
        />
      </div>
    </div>
  );
}
