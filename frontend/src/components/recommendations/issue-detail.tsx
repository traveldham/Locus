"use client";

import { Badge } from "@/components/tailgrids/core/badge";
import type {
  AuditLocation,
  RecommendationRun,
} from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import { Fragment, useState } from "react";
import { SEVERITY_COLOR, TONE_TEXT } from "./audit-format";
import { sectionHref } from "./audit-nav";
import { EvidencePanel } from "./evidence-panel";
import { issueSentence, plural } from "./issue-row";

const PAGE_SIZE = 25;

export function IssueDetail({
  run,
  location,
  rule,
}: {
  run: RecommendationRun;
  location: AuditLocation;
  rule: string;
}) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [openKey, setOpenKey] = useState<string | null>(null);

  const cluster = location.by_rule.find((row) => row.rule === rule);
  if (!cluster) {
    return (
      <p className="text-sm text-text-secondary">
        No check called “{rule}” exists in this audit.{" "}
        <Link href={sectionHref(location.id, "/issues")} className="underline">
          Back to all issues
        </Link>
      </p>
    );
  }

  const first = run.items.find(
    (item) => item.rule === rule && item.location_id === location.id,
  );
  const sentence = issueSentence(cluster, first?.why);
  if (cluster.issues === 0) {
    return (
      <div className="space-y-5">
        <Link
          href={sectionHref(location.id, "/issues")}
          className="inline-flex min-h-11 items-center gap-2 text-sm text-text-secondary underline-offset-4 hover:underline focus-visible:outline-primary-500"
        >
          ← All issues
        </Link>
        <div className="rounded-xl border border-card-border bg-card-background px-5 py-6">
          <h1 className="text-lg font-semibold tracking-[-0.015em] text-text-primary">
            {cluster.label}
          </h1>
          <p className="mt-1 text-xs text-text-tertiary">
            {cluster.category_label} · {location.name}
          </p>
          <p
            className={cn(
              "mt-4 text-sm font-medium",
              cluster.state === "clear" ? TONE_TEXT.success : TONE_TEXT.muted,
            )}
          >
            {cluster.state === "clear"
              ? "This check passed."
              : cluster.state === "suppressed"
                ? "This check does not apply to this profile."
                : "This check could not be evaluated."}
          </p>
          {cluster.reason ? (
            <p className="mt-1 text-sm leading-6 text-text-secondary">
              {cluster.reason}
            </p>
          ) : null}
          <div className="mt-5 grid gap-4 border-t border-card-border pt-4 text-sm leading-6 sm:grid-cols-2">
            <div>
              <h2 className="font-medium text-text-primary">
                About this check
              </h2>
              <p className="mt-1 text-text-secondary">{cluster.checks}</p>
            </div>
            <div>
              <h2 className="font-medium text-text-primary">How to fix</h2>
              <p className="mt-1 text-text-secondary">{cluster.fix}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }
  const term = search.trim().toLowerCase();
  const findings = run.items
    .filter((item) => item.rule === rule && item.location_id === location.id)
    .filter(
      (item) =>
        !term ||
        `${item.location_name} ${item.subject} ${item.why}`
          .toLowerCase()
          .includes(term),
    );
  const pages = Math.max(1, Math.ceil(findings.length / PAGE_SIZE));
  const visible = findings.slice(
    page * PAGE_SIZE,
    page * PAGE_SIZE + PAGE_SIZE,
  );
  const examined = cluster.subjects_examined;
  const failed = cluster.subjects_failed;
  const passed = Math.max(0, examined - failed);

  return (
    <div className="space-y-5">
      <Link
        href={sectionHref(location.id, "/issues")}
        className="inline-flex min-h-11 items-center gap-2 text-sm text-text-secondary underline-offset-4 hover:underline focus-visible:outline-primary-500"
      >
        ← All issues
      </Link>

      <div className="rounded-xl border border-card-border bg-card-background">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-card-border px-5 py-4">
          <div className="min-w-0">
            <h1 className="text-lg font-semibold tracking-[-0.015em] text-text-primary">
              {sentence.countable
                ? `${sentence.count} ${sentence.predicate}`
                : sentence.count}
            </h1>
            <p className="mt-1 text-xs text-text-tertiary">
              {cluster.category_label} · {location.name}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {cluster.worst_severity ? (
              <Badge color={SEVERITY_COLOR[cluster.worst_severity]} size="md">
                {cluster.worst_severity}
              </Badge>
            ) : null}
          </div>
        </div>

        <div className="grid gap-5 px-5 py-4 sm:grid-cols-[1fr_auto] sm:items-center">
          <div className="grid gap-4 text-sm leading-6 sm:grid-cols-2">
            <div>
              <h2 className="font-medium text-text-primary">
                About this check
              </h2>
              <p className="mt-1 text-text-secondary">{cluster.checks}</p>
            </div>
            <div>
              <h2 className="font-medium text-text-primary">How to fix</h2>
              <p className="mt-1 text-text-secondary">{cluster.fix}</p>
            </div>
          </div>
          <div className="sm:w-56">
            {cluster.subject ? (
              <>
                <p className="text-sm">
                  <span className={cn("font-medium", TONE_TEXT.error)}>
                    Failed: {failed}
                  </span>{" "}
                  <span className={cn("ml-2 font-medium", TONE_TEXT.success)}>
                    Passed: {passed}
                  </span>
                </p>
                <div
                  className="mt-2 flex h-2 overflow-hidden rounded-full bg-background-gray-secondary"
                  role="presentation"
                >
                  {examined ? (
                    <>
                      <div
                        className="bg-badge-error-text"
                        style={{ width: `${(failed / examined) * 100}%` }}
                      />
                      <div
                        className="bg-badge-success-text"
                        style={{ width: `${(passed / examined) * 100}%` }}
                      />
                    </>
                  ) : null}
                </div>
                <p className="mt-2 text-xs leading-5 text-text-tertiary">
                  {examined
                    ? `${plural(examined, cluster.subject)} examined.`
                    : "Nothing could be examined."}
                </p>
              </>
            ) : (
              // Nothing countable behind this check: its own wording says more than a bar.
              <p className="text-sm leading-6 text-text-secondary">
                {first?.why ??
                  "This check reports a single verdict for the profile."}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label className="sr-only" htmlFor="finding-search">
          Search affected subjects
        </label>
        <input
          id="finding-search"
          type="search"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(0);
          }}
          placeholder="Search subjects"
          className="min-h-9 w-64 rounded-lg border border-card-border bg-card-background px-3 text-sm text-text-primary focus-visible:outline-primary-500"
        />
        <span className="text-sm text-text-tertiary">
          {findings.length} of {cluster.issues} shown
        </span>
      </div>

      <div className="overflow-hidden rounded-xl border border-card-border bg-card-background">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-card-border text-left">
              <th
                scope="col"
                className="px-5 py-3 font-medium text-text-tertiary"
              >
                {cluster.unit === "location"
                  ? "Location"
                  : cluster.unit[0].toUpperCase() + cluster.unit.slice(1)}
              </th>
              <th
                scope="col"
                className="px-3 py-3 font-medium text-text-tertiary"
              >
                What was found
              </th>
              <th
                scope="col"
                className="w-28 px-5 py-3 text-right font-medium text-text-tertiary"
              >
                Severity
              </th>
            </tr>
          </thead>
          <tbody>
            {visible.map((item) => (
              <Fragment key={item.key}>
                <tr className="border-b border-card-border">
                  <th
                    scope="row"
                    className="px-5 py-3 text-left align-top font-normal text-text-primary"
                  >
                    {cluster.unit === "location"
                      ? item.location_name
                      : item.subject}
                  </th>
                  <td className="px-3 py-3 align-top text-text-secondary">
                    {item.why}
                    <button
                      type="button"
                      aria-expanded={openKey === item.key}
                      onClick={() =>
                        setOpenKey(openKey === item.key ? null : item.key)
                      }
                      className="ml-2 text-text-tertiary underline decoration-dotted underline-offset-4 hover:text-text-primary focus-visible:outline-primary-500"
                    >
                      {openKey === item.key ? "Hide evidence" : "Evidence"}
                    </button>
                  </td>
                  <td className="px-5 py-3 text-right align-top">
                    <Badge color={SEVERITY_COLOR[item.severity]} size="sm">
                      {item.severity}
                    </Badge>
                  </td>
                </tr>
                {openKey === item.key ? (
                  <tr className="border-b border-card-border">
                    <td
                      colSpan={3}
                      className="bg-background-gray-secondary px-5 pb-4"
                    >
                      <p className="pt-3 text-sm leading-6 text-text-primary">
                        {item.action}
                      </p>
                      <EvidencePanel runId={run.id} item={item} />
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            ))}
            {!visible.length ? (
              <tr>
                <td colSpan={3} className="px-5 py-8 text-text-secondary">
                  Nothing matches this search.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
        {pages > 1 ? (
          <div className="flex flex-wrap items-center gap-4 border-t border-card-border px-5 py-3 text-sm text-text-secondary">
            <span>
              Page {page + 1} of {pages}
            </span>
            <button
              type="button"
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
              className="min-h-11 underline disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={page + 1 >= pages}
              onClick={() => setPage(page + 1)}
              className="min-h-11 underline disabled:opacity-40"
            >
              Next
            </button>
          </div>
        ) : null}
      </div>
    </div>
  );
}
