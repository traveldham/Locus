"use client";

import type { AuditJob, AuditWorker } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";

const WORKER_TONE: Record<AuditWorker["status"], string> = {
  pending: "bg-text-disable",
  running: "bg-primary-500 animate-pulse",
  succeeded: "bg-badge-success-text",
  failed: "bg-badge-error-text",
};

const WORKER_TEXT: Record<AuditWorker["status"], string> = {
  pending: "Queued",
  running: "Running",
  succeeded: "Done",
  failed: "Failed",
};

/** Live status of one audit pipeline and the six workers inside it. */
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
          {job.error ?? "The worker stopped without recording a reason."}
          {hasPrevious
            ? " The audit below is the last one that completed."
            : ""}
        </p>
        <WorkerList workers={job.workers} />
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
      <WorkerList workers={job.workers} />
    </div>
  );
}

/** One line per worker. Progress above is how many of these have finished. */
function WorkerList({ workers }: { workers: AuditWorker[] }) {
  if (!workers.length) return null;
  return (
    <ul className="mt-3 grid gap-x-6 gap-y-1.5 text-xs sm:grid-cols-2 lg:grid-cols-3">
      {workers.map((worker) => (
        <li key={worker.category} className="flex items-center gap-2">
          <span
            className={cn(
              "size-2 shrink-0 rounded-full",
              WORKER_TONE[worker.status],
            )}
            aria-hidden="true"
          />
          <span className="text-text-primary">{worker.label}</span>
          <span className="ml-auto text-text-tertiary">
            {worker.status === "failed" && worker.error
              ? worker.error
              : WORKER_TEXT[worker.status]}
          </span>
        </li>
      ))}
    </ul>
  );
}
