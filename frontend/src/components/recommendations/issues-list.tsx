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
  "min-h-9 rounded-full border px-3 text-sm whitespace-nowrap transition focus-visible:outline-primary-500";

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
  const shown = severity
    ? failing.filter((rule) => rule.severity[severity])
    : failing;

  return (
    <div className="space-y-5">
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
          className="min-h-9 w-56 rounded-lg border border-card-border bg-card-background px-3 text-sm text-text-primary focus-visible:outline-primary-500"
        />
        <div
          className="flex flex-wrap gap-1.5"
          role="group"
          aria-label="Filter by area"
        >
          <Chip active={!area} onClick={() => setParam("area", "")}>
            All {failing.length}
          </Chip>
          {run.categories.map((category) => {
            const count = location.by_rule.filter(
              (rule) => rule.category === category.category && rule.issues > 0,
            ).length;
            if (!count) return null;
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
        {withIssuesOnly ? (
          <button
            type="button"
            onClick={() => setParam("checks", "all")}
            className="flex min-h-9 items-center gap-2 rounded-lg border border-primary-500 px-3 text-sm text-text-primary focus-visible:outline-primary-500"
          >
            With issues
            <span aria-hidden="true">✕</span>
            <span className="sr-only">Remove filter and show every check</span>
          </button>
        ) : (
          <button
            type="button"
            onClick={() => setParam("checks", "")}
            className="min-h-9 rounded-lg border border-card-border px-3 text-sm text-text-tertiary hover:text-text-primary focus-visible:outline-primary-500"
          >
            Show issues only
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
                  />
                ))}
              </ul>
            </section>
          );
        })}

        {!shown.length ? (
          <p className="px-5 py-8 text-sm text-text-secondary">
            No check matches this filter.
          </p>
        ) : null}

        {!withIssuesOnly && quiet.length ? (
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
