"use client";

import { SectionCard } from "@/components/common/section-card";
import type { AuditLocation, Severity } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import { SEVERITY_ORDER, TONE_TEXT } from "./audit-format";
import { issueHref, sectionHref, withParam } from "./audit-nav";
import { issueSentence } from "./issue-row";
import { ScoreBar, ScoreRing } from "./score-ring";

const SEVERITY_TONE = {
  critical: "error",
  warning: "warning",
  notice: "muted",
} as const;
const RANK: Record<Severity, number> = { critical: 0, warning: 1, notice: 2 };

export function LocationOverview({ location }: { location: AuditLocation }) {
  const health = location.health;

  const severityCount = (level: Severity) =>
    location.by_rule.reduce(
      (sum, rule) => sum + (rule.severity[level] ?? 0),
      0,
    );

  const top = [...location.by_rule]
    .filter((rule) => rule.issues > 0)
    .sort(
      (a, b) =>
        RANK[a.worst_severity ?? "notice"] -
          RANK[b.worst_severity ?? "notice"] || b.issues - a.issues,
    )
    .slice(0, 5);

  const checks = [
    {
      label: "Passed",
      value: health.checks_passed,
      fill: "bg-badge-success-text",
    },
    {
      label: "Found an issue",
      value: health.checks_failed,
      fill: "bg-badge-error-text",
    },
    {
      label: "Not evaluated",
      value: health.checks_not_evaluated,
      fill: "bg-text-disable",
    },
  ];
  const totalChecks = checks.reduce((sum, row) => sum + row.value, 0);

  return (
    <div className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-3">
        <SectionCard title="Health score">
          <ScoreRing
            score={health.score}
            grade={health.grade}
            label={
              health.score === null
                ? "No category has checks yet, so there is nothing to score."
                : `${Math.round(health.coverage * 100)}% of checks had enough evidence to run.`
            }
          />
          <p className="mt-4 border-t border-card-border pt-3 text-xs leading-5 text-text-tertiary">
            {health.basis}
          </p>
        </SectionCard>

        <SectionCard title="Checks run">
          <p className="text-[34px] leading-10 font-semibold tracking-[-0.03em] text-text-primary">
            {totalChecks}
          </p>
          <div
            className="mt-4 flex h-2.5 w-full overflow-hidden rounded-full bg-background-gray-secondary"
            role="presentation"
          >
            {checks.map((row) =>
              row.value ? (
                <div
                  key={row.label}
                  className={row.fill}
                  style={{ width: `${(row.value / totalChecks) * 100}%` }}
                />
              ) : null,
            )}
          </div>
          <dl className="mt-4 space-y-2.5">
            {checks.map((row) => (
              <div
                key={row.label}
                className="flex items-center gap-2.5 text-sm"
              >
                <span
                  className={`size-2.5 shrink-0 rounded-full ${row.fill}`}
                  aria-hidden="true"
                />
                <dt className="text-text-secondary">{row.label}</dt>
                <dd className="ml-auto font-medium text-text-primary">
                  {row.value}
                </dd>
              </div>
            ))}
          </dl>
          <p className="mt-4 border-t border-card-border pt-3 text-xs leading-5 text-text-tertiary">
            A check without enough evidence is left out of the score, not
            counted as a pass.
          </p>
        </SectionCard>

        <SectionCard title="Scores by category">
          <ul className="space-y-3.5">
            {health.categories.map((row) => (
              <li key={row.category}>
                <div className="flex flex-wrap items-baseline justify-between gap-x-3">
                  <span className="text-sm text-text-primary">
                    {row.label}
                    <span className="ml-1.5 text-xs text-text-tertiary">
                      {row.weight}%
                    </span>
                  </span>
                  <span className="text-xs text-text-tertiary">
                    {row.score === null
                      ? "not evaluated"
                      : `${row.issues} ${row.issues === 1 ? "issue" : "issues"}`}
                  </span>
                </div>
                <ScoreBar score={row.score} className="mt-1.5" />
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>

      <div className="grid gap-5 sm:grid-cols-3">
        {SEVERITY_ORDER.map((level) => {
          const count = severityCount(level);
          return (
            <SectionCard
              key={level}
              title={level[0].toUpperCase() + level.slice(1)}
            >
              <div className="flex items-baseline gap-2">
                <Link
                  href={withParam(
                    sectionHref(location.id, "/issues"),
                    "severity",
                    level,
                  )}
                  className={cn(
                    "text-[32px] leading-10 font-semibold tracking-[-0.03em] underline-offset-4 hover:underline",
                    TONE_TEXT[SEVERITY_TONE[level]],
                  )}
                >
                  {count}
                </Link>
              </div>
            </SectionCard>
          );
        })}
      </div>

      <SectionCard
        title="Top issues"
        bodyClassName="px-0 py-0"
        actions={
          <Link
            href={sectionHref(location.id, "/issues")}
            className="min-h-11 text-sm text-text-secondary underline underline-offset-4 focus-visible:outline-primary-500"
          >
            View all issues
          </Link>
        }
      >
        <ul>
          {top.map((rule) => {
            const sentence = issueSentence(rule);
            return (
              <li
                key={rule.rule}
                className="flex flex-wrap items-center gap-x-3 border-b border-card-border px-5 py-3.5 text-sm last:border-b-0"
              >
                <p className="min-w-0 flex-1 leading-6 text-text-primary">
                  <Link
                    href={issueHref(location.id, rule.rule)}
                    className="font-medium text-primary-500 underline-offset-4 hover:underline"
                  >
                    {sentence.count}
                  </Link>{" "}
                  {sentence.predicate}
                </p>
                <span
                  className={cn(
                    "text-xs",
                    TONE_TEXT[SEVERITY_TONE[rule.worst_severity ?? "notice"]],
                  )}
                >
                  {rule.worst_severity}
                </span>
              </li>
            );
          })}
          {!top.length ? (
            <li className="px-5 py-8 text-sm text-text-secondary">
              No check found an issue at this location.
            </li>
          ) : null}
        </ul>
      </SectionCard>
    </div>
  );
}
