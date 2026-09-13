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
  const { run, inputsChanged, isPending, job, isAuditing, trackJob } =
    useAuditRun(locationId);
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
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <nav aria-label="Breadcrumb" className="text-sm text-text-tertiary">
        <Link
          href={AUDIT_ROOT}
          className="underline-offset-4 hover:text-text-primary hover:underline focus-visible:outline-primary-500"
        >
          All locations
        </Link>
      </nav>

      <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-[26px] leading-8 font-semibold tracking-[-0.03em] text-text-primary sm:text-[28px]">
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
          {run && location ? (
            <p className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-text-tertiary">
              <span className={cn("font-medium", TONE_TEXT[scoreTone(score)])}>
                {score ?? "—"}/100 {GRADE_LABEL[location.health.grade]}
              </span>
              <span>·</span>
              <span>As of {run.as_of}</span>
              <span>·</span>
              <span>
                Updated {new Date(run.created_at).toLocaleDateString()}
              </span>
              <span>·</span>
              <span>Engine {run.engine_version}</span>
              <span>·</span>
              <span>
                {location.health.checks_passed + location.health.checks_failed}{" "}
                of{" "}
                {location.health.checks_passed +
                  location.health.checks_failed +
                  location.health.checks_not_evaluated}{" "}
                checks ran
              </span>
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
              size="lg"
              isDisabled={generate.isPending || isAuditing}
            >
              {isAuditing
                ? "Audit running…"
                : generate.isPending
                  ? "Queueing…"
                  : "Rerun audit"}
            </Button>
            <span className="text-xs text-text-tertiary">
              This profile only
            </span>
          </form>
        </div>
      </div>

      <AuditProgress job={job} hasPrevious={Boolean(run)} />

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
          Your data has changed since this audit ran. Rerun it to update the
          scores; the saved evidence still belongs to the previous run.
        </p>
      ) : null}

      <nav
        aria-label="Audit sections"
        className="mt-6 border-b border-card-border"
      >
        <ul className="-mb-px flex flex-wrap gap-x-1">
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
                    "flex h-11 items-center gap-2 rounded-t-lg border-b-2 px-3 text-sm font-medium transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
                    isActive
                      ? "border-primary-500 text-text-primary"
                      : "border-transparent text-text-tertiary hover:text-text-primary",
                  )}
                >
                  {section.label}
                  {count === undefined ? null : (
                    <span className="text-xs text-text-tertiary">{count}</span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="mt-6">{children}</div>
    </div>
  );
}
