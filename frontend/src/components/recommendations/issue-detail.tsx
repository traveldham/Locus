"use client";

import { Badge } from "@/components/tailgrids/core/badge";
import type {
  AuditLocation,
  RecommendationRun,
} from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import { useState } from "react";
import { SEVERITY_COLOR, TONE_TEXT } from "./audit-format";
import { sectionHref } from "./audit-nav";
import { EvidencePanel } from "./evidence-panel";
import { SuggestionPanel } from "./suggestion-panel";
import { issueSentence, plural } from "./issue-row";

const PAGE_SIZE = 25;

/** Why a finding has no draft: the honest reason, not a blanket excuse. */
function noDraftReason(
  suggests: string | null | undefined,
  status: { status: string; reason?: string; error?: string } | undefined,
) {
  if (!suggests) {
    return "No AI draft is shown because this fix needs information only the business can confirm.";
  }
  if (status?.status === "failed") {
    return `A draft was possible but could not be generated this time: ${status.error ?? "the model did not answer"}. Rerun the audit to try again.`;
  }
  if (status?.status === "skipped") {
    return `No draft was generated: ${status.reason ?? "drafts are not configured"}.`;
  }
  return "The model returned no usable draft for this finding. Rerun the audit to try again.";
}

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
  const currentPage = Math.min(page, pages - 1);
  const visible = findings.slice(
    currentPage * PAGE_SIZE,
    currentPage * PAGE_SIZE + PAGE_SIZE,
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
          className="min-h-11 w-full rounded-lg border border-card-border bg-card-background px-3 text-sm text-text-primary focus-visible:outline-primary-500 sm:w-64"
        />
        <span className="text-sm text-text-tertiary">
          {findings.length} of {cluster.issues} shown
        </span>
      </div>

      <div className="space-y-4">
        {visible.map((item) => (
          <article
            key={`${run.id}:${item.key}`}
            className="rounded-xl border border-card-border bg-card-background px-5 py-5"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs text-text-tertiary">
                  {cluster.unit === "location"
                    ? item.location_name
                    : item.subject}
                </p>
                <h2 className="mt-1 text-base font-semibold text-text-primary">
                  {item.title}
                </h2>
              </div>
              <Badge color={SEVERITY_COLOR[item.severity]} size="sm">
                {item.severity}
              </Badge>
            </div>

            <div className="mt-4">
              <h3 className="text-sm font-medium text-text-primary">
                What to do
              </h3>
              <p className="mt-1 text-sm leading-6 text-text-secondary">
                {item.action}
              </p>
            </div>

            {item.suggestion ? (
              <div className="mt-4">
                <SuggestionPanel
                  suggestion={item.suggestion}
                  locationId={location.id}
                />
              </div>
            ) : (
              <p className="mt-4 rounded-lg bg-background-gray-secondary px-4 py-3 text-xs leading-5 text-text-tertiary">
                {noDraftReason(
                  cluster.suggests,
                  location.suggestions?.[cluster.category],
                )}
              </p>
            )}

            <div className="mt-4 border-t border-card-border pt-4">
              <EvidencePanel runId={run.id} item={item} />
            </div>
          </article>
        ))}
        {!visible.length ? (
          <p className="rounded-xl border border-card-border bg-card-background px-5 py-8 text-sm text-text-secondary">
            Nothing matches this search.
          </p>
        ) : null}
        {pages > 1 ? (
          <div className="flex flex-wrap items-center gap-4 py-2 text-sm text-text-secondary">
            <span>
              Page {currentPage + 1} of {pages}
            </span>
            <button
              type="button"
              disabled={currentPage === 0}
              onClick={() => setPage(currentPage - 1)}
              className="min-h-11 underline disabled:opacity-40"
            >
              Previous
            </button>
            <button
              type="button"
              disabled={currentPage + 1 >= pages}
              onClick={() => setPage(currentPage + 1)}
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
