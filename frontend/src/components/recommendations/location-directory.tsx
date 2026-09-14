"use client";

import { SectionCard } from "@/components/common/section-card";
import { Badge } from "@/components/tailgrids/core/badge";
import { Button } from "@/components/tailgrids/core/button";
import { useGenerateRecommendations } from "@/hooks/use-recommendations";
import type { DirectoryRow } from "@/services/api/recommendations";
import Link from "next/link";
import { useState } from "react";
import { SEVERITY_COLOR, SEVERITY_ORDER } from "./audit-format";
import { locationRoot } from "./audit-nav";
import { auditStage } from "./audit-progress";
import { ScoreBar } from "./score-ring";

/** One location, one saved report. The list stays readable on narrow screens. */
export function LocationDirectory({ rows }: { rows: DirectoryRow[] }) {
  const generate = useGenerateRecommendations();
  const [search, setSearch] = useState("");
  const shown = rows.filter((row) =>
    `${row.name} ${row.source_location_id ?? ""}`
      .toLowerCase()
      .includes(search.trim().toLowerCase()),
  );
  return (
    <SectionCard title={`Your profiles · ${rows.length}`} bodyClassName="p-0">
      <div className="border-b border-card-border px-5 py-4">
        <label htmlFor="audit-location-search" className="sr-only">
          Find a profile
        </label>
        <input
          id="audit-location-search"
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Find a profile"
          className="min-h-11 w-full rounded-lg border border-card-border bg-card-background px-3 text-sm text-text-primary focus-visible:outline-primary-500 sm:max-w-sm"
        />
      </div>
      <ul className="divide-y divide-card-border">
        {shown.map((row) => {
          const running =
            row.job?.status === "pending" || row.job?.status === "running";
          return (
            <li
              key={row.location_id}
              className="grid items-center gap-5 px-5 py-5 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1.5fr)_auto]"
            >
              <div className="min-w-0">
                <Link
                  href={locationRoot(row.location_id)}
                  className="inline-flex min-h-11 items-center text-base font-semibold break-words text-text-primary underline-offset-4 hover:underline focus-visible:outline-primary-500"
                >
                  {row.name}
                </Link>
                <p className="text-xs leading-5 text-text-secondary">
                  {running && row.job
                    ? auditStage(row.job)
                    : row.audited_at
                      ? `Audited ${new Date(row.audited_at).toLocaleString()}`
                      : "Ready for its first audit"}
                </p>
                {running && row.audited_at ? (
                  <p className="mt-1 text-xs text-text-tertiary">
                    Showing the previous report while the new audit runs.
                  </p>
                ) : null}
              </div>
              <div className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)] gap-5">
                <div>
                  <p className="mb-2 text-xs font-medium text-text-secondary">
                    Profile health
                  </p>
                  {row.score === null ? (
                    <p className="text-sm text-text-secondary">
                      {row.audited_at ? "Not enough evidence" : "Not audited"}
                    </p>
                  ) : (
                    <ScoreBar score={row.score} />
                  )}
                  {row.coverage !== null ? (
                    <p className="mt-2 text-xs text-text-tertiary">
                      {Math.round(row.coverage * 100)}% of checks evaluated
                    </p>
                  ) : null}
                </div>
                <div>
                  <p className="mb-2 text-xs font-medium text-text-secondary">
                    Findings to review
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {SEVERITY_ORDER.map((severity) =>
                      row.severity[severity] ? (
                        <Badge
                          key={severity}
                          color={SEVERITY_COLOR[severity]}
                          size="sm"
                        >
                          {row.severity[severity]} {severity}
                        </Badge>
                      ) : null,
                    )}
                    {row.issues === 0 ? (
                      <span className="text-sm text-text-secondary">
                        {row.score === null
                          ? "Checks not evaluated"
                          : "No findings in evaluated checks"}
                      </span>
                    ) : null}
                    {row.issues === null ? (
                      <span className="text-sm text-text-tertiary">
                        Available after the audit
                      </span>
                    ) : null}
                  </div>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Link
                  href={locationRoot(row.location_id)}
                  className="inline-flex min-h-11 items-center text-sm font-medium text-primary-500 underline underline-offset-4 focus-visible:outline-primary-500"
                >
                  {running
                    ? "Follow audit"
                    : row.audited_at
                      ? "View report"
                      : "View profile"}
                </Link>
                <Button
                  size="xl"
                  appearance="outline"
                  isDisabled={running || generate.isPending}
                  onPress={() => generate.mutate(row.location_id)}
                >
                  {running
                    ? "Auditing…"
                    : generate.isPending &&
                        generate.variables === row.location_id
                      ? "Starting…"
                      : row.audited_at
                        ? "Refresh"
                        : "Run audit"}
                </Button>
              </div>
            </li>
          );
        })}
      </ul>
      {!shown.length ? (
        <p className="px-5 py-8 text-sm text-text-secondary">
          {rows.length
            ? "No profiles match your search."
            : "Add a profile to your project to start reviewing it."}
        </p>
      ) : null}
      <div className="border-t border-card-border px-5 py-4 text-xs leading-6 text-text-secondary">
        {generate.error ? (
          <p role="alert" className="mb-2 text-badge-error-text">
            The audit could not be started. Try again. {generate.error.message}
          </p>
        ) : null}
        <p>
          Each profile has its own audit date. Scores use the checks that could
          be evaluated; missing evidence is never counted as a pass. Open a
          report to see every check and its supporting records.
        </p>
      </div>
    </SectionCard>
  );
}
