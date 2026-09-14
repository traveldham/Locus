"use client";

import type {
  AuditLocation,
  RecommendationRun,
  Severity,
} from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import { useRouter, useSearchParams } from "next/navigation";
import { SEVERITY_ORDER, TONE_TEXT } from "./audit-format";
import { IssueRow } from "./issue-row";

const chip =
  "min-h-11 rounded-lg border px-3 text-sm whitespace-nowrap motion-safe:transition-colors focus-visible:outline-primary-500";

const SEVERITY_RULE = {
  critical: "border-badge-error-text",
  warning: "border-badge-warning-text",
  notice: "border-text-disable",
} as const;

export function IssuesList({
  run,
  location,
}: {
  run: RecommendationRun;
  location: AuditLocation;
}) {
  const router = useRouter();
  const params = useSearchParams();
  const area = params.get("area") ?? "";
  const severity = (params.get("severity") ?? "") as Severity | "";
  const search = params.get("q") ?? "";
  const withIssuesOnly = params.get("checks") !== "all";
  const draftsOnly = params.get("drafts") === "1";

  // Counted from the findings, because `RuleCluster.suggests` only names the field a
  // check may draft: it says nothing about whether this run actually produced one.
  const draftsByRule = new Map<string, number>();
  for (const item of run.items) {
    if (item.suggestion)
      draftsByRule.set(item.rule, (draftsByRule.get(item.rule) ?? 0) + 1);
  }

  function setParam(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    router.replace(`?${next.toString()}`, { scroll: false });
  }

  const term = search.trim().toLowerCase();
  const matching = location.by_rule.filter((rule) => {
    if (area && rule.category !== area) return false;
    if (!term) return true;
    return `${rule.label} ${rule.checks} ${rule.predicate}`
      .toLowerCase()
      .includes(term);
  });
  const failing = matching.filter((rule) => rule.issues > 0);
  const quiet = matching.filter((rule) => rule.issues === 0);
  const bySeverity = severity
    ? failing.filter((rule) => rule.severity[severity])
    : failing;
  const drafted = bySeverity.filter((rule) => draftsByRule.has(rule.rule));
  const shown = draftsOnly ? drafted : bySeverity;

  return (
    <div className="space-y-5">
      <div>
        <h2 className="text-xl font-semibold tracking-[-0.02em] text-text-primary">
          Your findings and next steps
        </h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-text-secondary">
          Start with the checks needing attention. Open a finding to see the
          affected items, the evidence and any draft you can review.
        </p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <label className="sr-only" htmlFor="issue-search">
          Search checks
        </label>
        <input
          id="issue-search"
          type="search"
          defaultValue={search}
          onChange={(e) => setParam("q", e.target.value)}
          placeholder="Search checks"
          className="min-h-11 w-full rounded-lg border border-card-border bg-card-background px-3 text-sm text-text-primary focus-visible:outline-primary-500 sm:w-56"
        />
        <div
          className="flex flex-wrap gap-1.5"
          role="group"
          aria-label="Filter by area"
        >
          <Chip active={!area} onClick={() => setParam("area", "")}>
            All areas
          </Chip>
          {run.categories.map((category) => {
            const count = location.by_rule.filter(
              (rule) => rule.category === category.category && rule.issues > 0,
            ).length;
            return (
              <Chip
                key={category.category}
                active={area === category.category}
                onClick={() =>
                  setParam(
                    "area",
                    area === category.category ? "" : category.category,
                  )
                }
              >
                {category.label} {count}
              </Chip>
            );
          })}
        </div>
        <div
          className="ml-auto flex flex-wrap gap-1.5"
          role="group"
          aria-label="Filter by severity"
        >
          <Chip active={!severity} onClick={() => setParam("severity", "")}>
            All {failing.length}
          </Chip>
          {SEVERITY_ORDER.map((level) => {
            const count = failing.filter((rule) => rule.severity[level]).length;
            return (
              <Chip
                key={level}
                active={severity === level}
                onClick={() =>
                  setParam("severity", severity === level ? "" : level)
                }
              >
                {level} {count}
              </Chip>
            );
          })}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {draftsByRule.size ? (
          <Chip
            active={draftsOnly}
            onClick={() => setParam("drafts", draftsOnly ? "" : "1")}
          >
            With an AI draft {drafted.length}
          </Chip>
        ) : null}
        {withIssuesOnly ? (
          <button
            type="button"
            onClick={() => setParam("checks", "all")}
            className="flex min-h-11 items-center gap-2 rounded-lg border border-primary-500 px-3 text-sm text-text-primary focus-visible:outline-primary-500"
          >
            Show passed and unevaluated checks too
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setParam("checks", "")}
            className="min-h-11 rounded-lg border border-card-border px-3 text-sm text-text-tertiary hover:text-text-primary focus-visible:outline-primary-500"
          >
            Show checks needing attention only
          </button>
        )}
      </div>

      <div className="rounded-xl border border-card-border bg-card-background">
        {SEVERITY_ORDER.map((level) => {
          const group = shown.filter((rule) => rule.worst_severity === level);
          if (!group.length) return null;
          return (
            <section key={level}>
              <h2
                className={cn(
                  "border-b-2 px-5 py-3 text-sm font-semibold text-text-primary",
                  SEVERITY_RULE[level],
                )}
              >
                <span
                  className={
                    TONE_TEXT[
                      level === "notice"
                        ? "muted"
                        : level === "critical"
                          ? "error"
                          : "warning"
                    ]
                  }
                >
                  {level[0].toUpperCase() + level.slice(1)}
                </span>{" "}
                <span className="text-text-tertiary">({group.length})</span>
              </h2>
              <ul>
                {group.map((rule) => (
                  <IssueRow
                    key={rule.rule}
                    rule={rule}
                    locationId={location.id}
                    why={run.items.find((item) => item.rule === rule.rule)?.why}
                    isNew={Boolean(
                      location.changes &&
                      !location.changes.first_audit &&
                      location.changes.new.includes(rule.rule),
                    )}
                    drafts={draftsByRule.get(rule.rule) ?? 0}
                  />
                ))}
              </ul>
            </section>
          );
        })}

        {!shown.length && (withIssuesOnly || draftsOnly || !quiet.length) ? (
          <p className="px-5 py-8 text-sm text-text-secondary">
            {draftsOnly
              ? "No check in this view arrived with a draft. Clear the draft filter to see the rest."
              : "No check matches this filter."}
          </p>
        ) : null}

        {/* A passed check has no finding and so can never carry a draft. */}
        {!withIssuesOnly && !draftsOnly && quiet.length ? (
          <section>
            <h2 className="border-b-2 border-badge-success-text px-5 py-3 text-sm font-semibold text-text-primary">
              <span className={TONE_TEXT.success}>Other checks</span>{" "}
              <span className="text-text-tertiary">({quiet.length})</span>
            </h2>
            <ul>
              {quiet.map((rule) => (
                <li
                  key={rule.rule}
                  className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-card-border px-5 py-3.5 text-sm last:border-b-0"
                >
                  <span className="flex-1 text-text-primary">{rule.label}</span>
                  <span className="text-text-tertiary">
                    {location.changes?.fixed.includes(rule.rule) ? (
                      <span
                        className={cn("mr-2 font-medium", TONE_TEXT.success)}
                      >
                        Fixed since last audit
                      </span>
                    ) : null}
                    {rule.state === "clear"
                      ? "Passed"
                      : rule.state === "suppressed"
                        ? "Not applicable"
                        : "Not evaluated"}
                    {rule.reason ? ` — ${rule.reason}` : ""}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>

      <p className="text-xs leading-5 text-text-tertiary">
        Issue counts refer to checks. Open a check to see every affected item
        and the saved records that support it.
      </p>
    </div>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        chip,
        active
          ? "border-primary-500 text-text-primary"
          : "border-card-border text-text-tertiary hover:text-text-primary",
      )}
    >
      {children}
    </button>
  );
}
