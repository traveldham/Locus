"use client";

import { Badge } from "@/components/tailgrids/core/badge";
import { Button } from "@/components/tailgrids/core/button";
import { useActiveProject } from "@/contexts/active-project";
import { useAuditRun } from "@/hooks/use-audit";
import {
  useAuditDirectory,
  useGenerateRecommendations,
} from "@/hooks/use-recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { GRADE_LABEL, TONE_TEXT, scoreTone } from "./audit-format";
import { AuditProgress } from "./audit-progress";
import {
  AUDIT_ROOT,
  AUDIT_SECTIONS,
  findLocation,
  sectionCounts,
  sectionHref,
} from "./audit-nav";

const control =
  "min-h-11 rounded-lg border border-card-border bg-card-background px-3 text-sm text-text-primary focus-visible:outline-primary-500";

/** The audit is always about one location. This frames it. */
export function LocationShell({
  locationId,
  children,
}: {
  locationId: string;
  children: ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const {
    run,
    inputsChanged,
    isPending,
    job,
    isAuditing,
    trackJob,
    jobError,
    refreshJob,
  } = useAuditRun(locationId);
  const generate = useGenerateRecommendations();
  // The switcher lists the active project's profiles, which no longer live inside one audit.
  const profiles =
    useAuditDirectory(useActiveProject().projectId).data?.items ?? [];
  const location = findLocation(run, locationId);
  // Before the first audit there is no run to take the name from, so fall back to the
  // directory, which knows every profile whether or not it has been audited.
  const name =
    location?.name ??
    profiles.find((row) => row.location_id === locationId)?.name ??
    (isPending ? "Loading…" : "Unknown location");
  const counts = sectionCounts(location);
  const score = location?.health.score ?? null;

  return (
    <div className="mx-auto max-w-[1440px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
      <nav aria-label="Breadcrumb" className="text-sm text-text-tertiary">
        <Link
          href={AUDIT_ROOT}
          className="inline-flex min-h-11 items-center underline-offset-4 hover:text-text-primary hover:underline focus-visible:outline-primary-500"
        >
          All locations
        </Link>
      </nav>

      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-[26px] leading-8 font-semibold tracking-[-0.03em] break-words text-text-primary sm:text-[28px]">
              {name}
            </h1>
            {profiles.length > 1 ? (
              <>
                <label className="sr-only" htmlFor="location-switcher">
                  Switch profile
                </label>
                <select
                  id="location-switcher"
                  value={locationId}
                  onChange={(e) => router.push(sectionHref(e.target.value, ""))}
                  className={cn(control, "max-w-56")}
                >
                  {profiles.map((row) => (
                    <option key={row.location_id} value={row.location_id}>
                      {row.name} · {row.score ?? "—"}
                    </option>
                  ))}
                </select>
              </>
            ) : null}
          </div>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-text-secondary">
            Your Google profile audit. Understand what customers find, what
            needs attention and what to improve next.
          </p>
          {run && location ? (
            <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-text-tertiary">
              <span className={cn("font-medium", TONE_TEXT[scoreTone(score)])}>
                {score ?? "—"}/100 {GRADE_LABEL[location.health.grade]}
              </span>
              <span>·</span>
              <span>Analysis date {run.as_of}</span>
              <span>·</span>
              <span>
                Updated {new Date(run.created_at).toLocaleDateString()}
              </span>
              <span>·</span>
              {location.source === "fixture" ? (
                <Badge color="blue" size="sm">
                  Sample data
                </Badge>
              ) : null}
            </p>
          ) : null}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <form
            className="flex flex-col items-end gap-1"
            onSubmit={(e) => {
              e.preventDefault();
              generate.mutate(locationId, {
                onSuccess: (queued) => trackJob(queued.id),
              });
            }}
          >
            <Button
              type="submit"
              size="xl"
              isDisabled={generate.isPending || isAuditing}
            >
              {isAuditing
                ? "Audit running…"
                : generate.isPending
                  ? "Starting audit…"
                  : job?.status === "failed"
                    ? "Try audit again"
                    : run
                      ? "Refresh audit"
                      : "Run first audit"}
            </Button>
            <span className="text-xs text-text-tertiary">
              Reviews all six areas for this location
            </span>
          </form>
        </div>
      </div>

      <AuditProgress
        job={job}
        hasPrevious={Boolean(run)}
        publishedRunId={run?.id}
      />

      {jobError ? (
        <div
          role="alert"
          className="mt-4 rounded-xl bg-badge-warning-background px-4 py-3 text-sm text-badge-warning-text"
        >
          We couldn’t refresh the audit status. The review may still be running.
          <button
            type="button"
            onClick={refreshJob}
            className="ml-2 inline-flex min-h-11 items-center font-medium underline focus-visible:outline-primary-500"
          >
            Check status again
          </button>
        </div>
      ) : null}

      {generate.error ? (
        <p role="alert" className="mt-4 text-sm text-badge-error-text">
          Audit failed: {generate.error.message}
        </p>
      ) : null}
      {inputsChanged && !isAuditing ? (
        <p
          role="status"
          className="mt-4 rounded-lg bg-badge-warning-background p-4 text-sm text-badge-warning-text"
        >
          Your data or audit checks have changed. Refresh the audit to update
          these results. The evidence shown belongs to the saved report.
        </p>
      ) : null}

      <nav
        aria-label="Audit sections"
        className="mt-6 rounded-xl border border-card-border bg-card-background p-1.5"
      >
        <label htmlFor="audit-section" className="sr-only">
          Choose an audit area
        </label>
        <select
          id="audit-section"
          className={cn(control, "w-full md:hidden")}
          value={
            [...AUDIT_SECTIONS]
              .reverse()
              .find((section) =>
                section.href
                  ? pathname.startsWith(
                      `${AUDIT_ROOT}/${locationId}${section.href}`,
                    )
                  : pathname === `${AUDIT_ROOT}/${locationId}`,
              )?.href ?? ""
          }
          onChange={(event) =>
            router.push(sectionHref(locationId, event.target.value))
          }
        >
          {AUDIT_SECTIONS.map((section) => {
            const count = counts[section.href as keyof typeof counts];
            return (
              <option key={section.href} value={section.href}>
                {section.label}
                {count ? ` · ${count} checks need attention` : ""}
              </option>
            );
          })}
        </select>
        <ul className="hidden flex-wrap gap-1 md:flex">
          {AUDIT_SECTIONS.map((section) => {
            const base = `${AUDIT_ROOT}/${locationId}${section.href}`;
            const isActive = section.href
              ? pathname.startsWith(base)
              : pathname === `${AUDIT_ROOT}/${locationId}`;
            const count = counts[section.href as keyof typeof counts];
            return (
              <li key={section.href}>
                <Link
                  href={sectionHref(locationId, section.href)}
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "flex min-h-11 items-center gap-2 rounded-lg px-3 text-sm font-medium outline-none focus-visible:ring-2 focus-visible:ring-primary-500 motion-safe:transition-colors motion-safe:duration-200",
                    isActive
                      ? "bg-background-gray-secondary text-text-primary"
                      : "text-text-secondary hover:bg-background-gray-secondary hover:text-text-primary",
                  )}
                >
                  {section.label}
                  {!count ? null : (
                    <span className="text-xs tabular-nums text-text-secondary">
                      <span className="sr-only">
                        checks needing attention:{" "}
                      </span>
                      {count}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="mt-6">{children}</div>
      {run ? (
        <details className="mt-8 border-t border-card-border text-sm text-text-secondary">
          <summary className="min-h-11 cursor-pointer py-3 focus-visible:outline-primary-500">
            About this report
          </summary>
          <p className="max-w-3xl pb-4 text-xs leading-6">
            Generated {new Date(run.created_at).toLocaleString()} · Analysis
            date {run.as_of} · Audit version {run.engine_version}. Scores come
            from the saved evidence and configured checks. AI drafts are
            suggestions to review; this audit does not publish changes to your
            Google profile.
          </p>
        </details>
      ) : null}
    </div>
  );
}
