"use client";

import { SectionCard } from "@/components/common/section-card";
import { Badge } from "@/components/tailgrids/core/badge";
import { Button } from "@/components/tailgrids/core/button";
import { useGenerateRecommendations } from "@/hooks/use-recommendations";
import type { DirectoryRow } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import {
  SEVERITY_COLOR,
  SEVERITY_ORDER,
  TONE_TEXT,
  scoreTone,
} from "./audit-format";
import { locationRoot } from "./audit-nav";
import { ScoreBar } from "./score-ring";

function audited(row: DirectoryRow): string {
  if (row.job) {
    return row.job.status === "pending"
      ? "Queued…"
      : `${row.job.stage} · ${row.job.progress}%`;
  }
  if (!row.audited_at) return "Never audited";
  return new Date(row.audited_at).toLocaleString();
}

/** Every profile with its own audit. Each is audited separately, on its own schedule. */
export function LocationDirectory({ rows }: { rows: DirectoryRow[] }) {
  const generate = useGenerateRecommendations();
  const never = rows.filter((row) => !row.audited_at).length;

  return (
    <SectionCard title={`Locations (${rows.length})`} bodyClassName="px-0 py-0">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[52rem] border-collapse text-sm">
          <thead>
            <tr className="border-b border-card-border text-left">
              <th
                scope="col"
                className="px-5 py-3 font-medium text-text-tertiary"
              >
                Location
              </th>
              <th
                scope="col"
                className="w-40 px-3 py-3 font-medium text-text-tertiary"
              >
                Health
              </th>
              <th
                scope="col"
                className="w-52 px-3 py-3 font-medium text-text-tertiary"
              >
                Issues
              </th>
              <th
                scope="col"
                className="w-24 px-3 py-3 font-medium text-text-tertiary"
              >
                Coverage
              </th>
              <th
                scope="col"
                className="w-48 px-3 py-3 font-medium text-text-tertiary"
              >
                Last audited
              </th>
              <th
                scope="col"
                className="w-32 px-5 py-3 text-right font-medium text-text-tertiary"
              >
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const running =
                row.job?.status === "pending" || row.job?.status === "running";
              return (
                <tr
                  key={row.location_id}
                  className="border-b border-card-border last:border-b-0 hover:bg-background-gray-secondary"
                >
                  <th scope="row" className="px-5 py-3 text-left font-normal">
                    {row.audited_at ? (
                      <Link
                        href={locationRoot(row.location_id)}
                        className="text-sm font-medium text-text-primary underline-offset-4 hover:underline focus-visible:outline-primary-500"
                      >
                        {row.name}
                      </Link>
                    ) : (
                      <span className="text-sm font-medium text-text-primary">
                        {row.name}
                      </span>
                    )}
                    {row.source_location_id ? (
                      <span className="block text-xs text-text-tertiary">
                        {row.source_location_id}
                      </span>
                    ) : null}
                  </th>
                  <td className="px-3 py-3">
                    {row.score === null ? (
                      <span className="text-text-disable">—</span>
                    ) : (
                      <ScoreBar score={row.score} />
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {SEVERITY_ORDER.map((severity) => {
                        const count = row.severity[severity];
                        if (!count) return null;
                        return (
                          <Badge
                            key={severity}
                            color={SEVERITY_COLOR[severity]}
                            size="sm"
                          >
                            {count} {severity}
                          </Badge>
                        );
                      })}
                      {row.issues === 0 ? (
                        <span className={cn("text-xs", TONE_TEXT.success)}>
                          No issues
                        </span>
                      ) : null}
                      {row.issues === null ? (
                        <span className="text-xs text-text-tertiary">
                          Not audited
                        </span>
                      ) : null}
                    </div>
                  </td>
                  <td className="px-3 py-3 text-text-secondary">
                    {row.coverage === null
                      ? "—"
                      : `${Math.round(row.coverage * 100)}%`}
                  </td>
                  <td className="px-3 py-3 text-text-secondary">
                    <span className={running ? TONE_TEXT.warning : undefined}>
                      {audited(row)}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <Link
                        href={locationRoot(row.location_id)}
                        className={cn(
                          "text-sm font-medium underline-offset-4 hover:underline focus-visible:outline-primary-500",
                          TONE_TEXT[scoreTone(row.score)],
                        )}
                      >
                        {row.audited_at ? "Open" : "View"}
                      </Link>
                      <Button
                        size="sm"
                        appearance="outline"
                        isDisabled={running || generate.isPending}
                        onPress={() => generate.mutate(row.location_id)}
                      >
                        {running
                          ? "Running…"
                          : row.audited_at
                            ? "Rerun"
                            : "Run audit"}
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="border-t border-card-border px-5 py-3 text-xs leading-5 text-text-tertiary">
        {generate.error ? (
          <p role="alert" className="text-badge-error-text">
            Could not queue that audit: {generate.error.message}
          </p>
        ) : null}
        <p>
          Each location is audited separately, so their scores can come from
          different moments. Coverage is the share of a location&apos;s checks
          that had enough evidence to run — a low number means under-measured,
          not healthy.
          {never
            ? ` ${never} location${never === 1 ? " has" : "s have"} never been audited.`
            : ""}
        </p>
      </div>
    </SectionCard>
  );
}
