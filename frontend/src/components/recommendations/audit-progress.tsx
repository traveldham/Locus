"use client";

import type { AuditJob, AuditWorker } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";

const AREA_DESCRIPTION: Record<string, string> = {
  profile: "Business details, opening hours and profile completeness",
  reputation: "Customer reviews, ratings and your responses",
  visibility: "Search visibility, keywords and local competitors",
  operations: "Appointment requests and follow-up",
  performance: "Profile views, calls, clicks and directions",
  content: "Photos, videos and recent posts",
};

export function auditStage(job: AuditJob): string {
  if (job.status === "pending") return "Your audit is in the queue";
  if (job.status === "failed") return "Your audit needs another try";
  if (job.status === "succeeded") return "Your audit is ready";
  if (
    job.workers.length &&
    job.workers.every((area) => area.status === "succeeded")
  )
    return "Putting your recommendations together";
  if (!job.workers.some((area) => area.status !== "pending"))
    return "Preparing your profile for review";
  return "Reviewing your Google profile";
}

function areaStage(area: AuditWorker): string {
  if (area.status === "succeeded") return "Reviewed";
  if (area.status === "failed") return "Could not complete";
  if (area.status === "pending") return "Up next";
  return area.stage === "Drafting suggestions"
    ? "Preparing suggestions"
    : "Checking your data";
}

function StatusMark({ status }: { status: AuditWorker["status"] }) {
  return (
    <span
      className={cn(
        "flex size-7 shrink-0 items-center justify-center rounded-full",
        status === "succeeded"
          ? "bg-badge-success-background text-badge-success-text"
          : status === "failed"
            ? "bg-badge-error-background text-badge-error-text"
            : status === "running"
              ? "bg-background-gray-secondary text-primary-500"
              : "bg-background-gray-secondary text-text-tertiary",
      )}
      aria-hidden="true"
    >
      {status === "succeeded" ? (
        <svg
          viewBox="0 0 20 20"
          fill="none"
          className="size-4"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path
            d="m4 10 4 4 8-8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      ) : status === "running" ? (
        <svg
          viewBox="0 0 20 20"
          fill="none"
          className="size-4 motion-safe:animate-spin"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <circle cx="10" cy="10" r="7" opacity=".2" />
          <path d="M10 3a7 7 0 0 1 7 7" strokeLinecap="round" />
        </svg>
      ) : status === "failed" ? (
        <svg
          viewBox="0 0 20 20"
          fill="none"
          className="size-4"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path d="M10 5v6m0 3v.1" strokeLinecap="round" />
        </svg>
      ) : (
        <span className="size-1.5 rounded-full bg-current" />
      )}
    </span>
  );
}

/** Status follows recorded work, never a simulated timer or predicted finish time. */
export function AuditProgress({
  job,
  hasPrevious = true,
  publishedRunId,
}: {
  job: AuditJob | null;
  hasPrevious?: boolean;
  publishedRunId?: string;
}) {
  if (!job) return null;
  const failed = job.status === "failed";
  const ready = job.status === "succeeded";
  const loadingReport = ready && job.run_id !== publishedRunId;
  const finished = job.workers.filter(
    (area) => area.status === "succeeded",
  ).length;
  const total = job.workers.length;
  const assembling = !failed && !ready && total > 0 && finished === total;

  if (ready && !loadingReport)
    return (
      <div
        role="status"
        className="mt-5 flex flex-wrap items-center gap-3 rounded-xl bg-badge-success-background px-4 py-3 text-sm text-badge-success-text"
      >
        <StatusMark status="succeeded" />
        <p>
          <span className="font-medium">Your audit is ready.</span> Explore the
          findings and choose what to improve first.
        </p>
      </div>
    );

  return (
    <section
      aria-label="Audit status"
      className="mt-6 overflow-hidden rounded-2xl border border-card-border bg-card-background"
    >
      <div className="px-5 py-5 sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 max-w-2xl">
            <h2
              role={failed ? "alert" : "status"}
              className={cn(
                "text-lg font-semibold tracking-[-0.02em]",
                failed ? "text-badge-error-text" : "text-text-primary",
              )}
            >
              {loadingReport
                ? "Loading your completed report"
                : auditStage(job)}
            </h2>
            <p className="mt-1.5 text-sm leading-6 text-text-secondary">
              {failed
                ? "We couldn’t finish this review. Select Try audit again above to start a fresh audit."
                : loadingReport
                  ? "The review has finished. Your new scores and recommendations will appear shortly."
                  : assembling
                    ? "All areas have been reviewed. We’re preparing the overall summary and your action plan."
                    : job.status === "pending"
                      ? "Your request is saved. The review starts as soon as capacity is available; you can leave this page and return."
                      : "We’re checking the saved data for this location and turning the findings into practical next steps."}
            </p>
          </div>
          {!failed && !loadingReport ? (
            <span className="shrink-0 rounded-lg bg-background-gray-secondary px-3 py-2 text-sm font-medium tabular-nums text-text-primary">
              {finished} of {total} areas reviewed
            </span>
          ) : null}
        </div>
        {!failed ? (
          <div
            className="mt-5 flex gap-1.5"
            aria-label={`${finished} of ${total} review areas complete`}
          >
            {job.workers.map((area) => (
              <div
                key={area.category}
                className={cn(
                  "h-1.5 flex-1 rounded-full motion-safe:transition-colors motion-safe:duration-500",
                  area.status === "succeeded"
                    ? "bg-badge-success-text"
                    : area.status === "running"
                      ? "bg-primary-500 motion-safe:animate-pulse"
                      : "bg-background-gray-secondary",
                )}
              />
            ))}
          </div>
        ) : null}
        {hasPrevious ? (
          <p className="mt-4 text-xs leading-5 text-text-tertiary">
            The report below is your previous audit. It stays available until
            the new report is ready.
          </p>
        ) : null}
      </div>
      {!loadingReport ? (
        <ul className="grid border-t border-card-border sm:grid-cols-2 lg:grid-cols-3">
          {job.workers.map((area) => (
            <li key={area.category} className="flex gap-3 px-5 py-4 sm:px-6">
              <StatusMark status={area.status} />
              <div className="min-w-0">
                <p className="text-sm font-medium text-text-primary">
                  {area.label}
                </p>
                <p
                  className={cn(
                    "mt-0.5 text-xs font-medium",
                    area.status === "succeeded"
                      ? "text-badge-success-text"
                      : area.status === "failed"
                        ? "text-badge-error-text"
                        : "text-text-secondary",
                  )}
                >
                  {areaStage(area)}
                </p>
                <p className="mt-1 text-xs leading-5 text-text-tertiary">
                  {AREA_DESCRIPTION[area.category]}
                </p>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
      {failed && job.error ? (
        <details className="border-t border-card-border px-5 sm:px-6">
          <summary className="flex min-h-11 cursor-pointer items-center text-sm text-text-secondary focus-visible:outline-primary-500">
            View error details
          </summary>
          <p className="pb-4 text-xs leading-5 break-words text-text-tertiary">
            {job.error}
          </p>
        </details>
      ) : null}
    </section>
  );
}
