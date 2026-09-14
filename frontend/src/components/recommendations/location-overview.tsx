"use client";

import { SectionCard } from "@/components/common/section-card";
import { Badge } from "@/components/tailgrids/core/badge";
import type {
  AuditLocation,
  RecommendationRun,
  ScorePoint,
} from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import { SEVERITY_COLOR, TONE_TEXT, scoreTone } from "./audit-format";
import { issueHref, sectionHref } from "./audit-nav";
import { CategoryRings } from "./category-rings";
import { ScoreRing } from "./score-ring";
import { ScoreTrend } from "./score-trend";

function InsightList({
  title,
  tone,
  points,
  labels,
  locationId,
}: {
  title: string;
  tone: "success" | "error";
  points: { category: string; text: string }[];
  labels: Map<string, string>;
  locationId: string;
}) {
  const dot =
    tone === "success" ? "bg-badge-success-text" : "bg-badge-error-text";
  const href = (category: string) =>
    category === "profile"
      ? sectionHref(locationId, "/profile")
      : sectionHref(locationId, `/category/${category}`);
  return (
    <div>
      <h3 className={cn("text-sm font-semibold", TONE_TEXT[tone])}>{title}</h3>
      {points.length ? (
        <ul className="mt-2 space-y-2">
          {points.map((point, index) => (
            <li
              key={`${point.category}-${index}`}
              className="flex gap-2.5 text-sm leading-6"
            >
              <span
                className={cn("mt-2 size-2 shrink-0 rounded-full", dot)}
                aria-hidden="true"
              />
              <span className="min-w-0">
                <span className="text-text-primary">{point.text}</span>{" "}
                <Link
                  href={href(point.category)}
                  className="inline-flex min-h-11 min-w-11 items-center text-xs text-text-secondary underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-primary-500"
                >
                  {labels.get(point.category) ?? point.category}
                </Link>
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-text-secondary">
          No {tone === "success" ? "strengths" : "priorities"} highlighted in
          this summary.
        </p>
      )}
    </div>
  );
}

const EFFORT_LABEL: Record<string, string> = {
  minutes: "a few minutes",
  hour: "about an hour",
  afternoon: "an afternoon",
};

export function LocationOverview({
  run,
  location,
  history,
}: {
  run: RecommendationRun;
  location: AuditLocation;
  history: ScorePoint[];
}) {
  const health = location.health;
  // The whole-audit paragraph. Per-category summaries live on their own tabs.
  const summary = location.summary ?? null;
  const changes = location.changes;
  const byKey = new Map(run.items.map((item) => [item.key, item]));
  const byRule = new Map(location.by_rule.map((row) => [row.rule, row]));
  const todo = (location.priorities ?? [])
    .map((key) => byKey.get(key))
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
  const failedDrafts = Object.entries(location.suggestions ?? {}).filter(
    ([, result]) => result.status === "failed",
  );
  const evaluated = health.checks_passed + health.checks_failed;
  const total = evaluated + health.checks_not_evaluated;
  const categoryLabels = new Map(
    run.categories.map((c) => [c.category, c.label]),
  );

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <SectionCard title="Your profile health">
          <ScoreRing
            score={health.score}
            grade={health.grade}
            label={
              health.score === null
                ? "There is not enough evidence to score this audit."
                : "A weighted score from the checks that could be evaluated."
            }
          />
          <dl className="mt-6 divide-y divide-card-border border-y border-card-border text-sm">
            <div className="flex justify-between gap-3 py-3">
              <dt className="text-text-secondary">Checks passed</dt>
              <dd className="font-semibold tabular-nums text-badge-success-text">
                {health.checks_passed}
              </dd>
            </div>
            <div className="flex justify-between gap-3 py-3">
              <dt className="text-text-secondary">Checks needing attention</dt>
              <dd
                className={cn(
                  "font-semibold tabular-nums",
                  health.checks_failed ? TONE_TEXT.error : "text-text-primary",
                )}
              >
                {health.checks_failed}
              </dd>
            </div>
            <div className="flex justify-between gap-3 py-3">
              <dt className="text-text-secondary">Not evaluated</dt>
              <dd className="font-semibold tabular-nums text-text-primary">
                {health.checks_not_evaluated}
              </dd>
            </div>
          </dl>
          <p className="mt-3 text-xs leading-5 text-text-secondary">
            {evaluated} of {total} checks had enough evidence to run. Missing
            evidence is excluded from the score.
          </p>
          <div className="mt-5 border-t border-card-border pt-4">
            <h3 className="mb-2 text-sm font-medium text-text-primary">
              Progress over time
            </h3>
            <ScoreTrend history={history} />
            {changes && !changes.first_audit ? (
              <p className="mt-3 text-xs leading-5 text-text-secondary">
                Since your previous audit:{" "}
                <span className={cn("font-medium", TONE_TEXT.success)}>
                  {changes.fixed.length} checks resolved
                </span>{" "}
                ·{" "}
                <span
                  className={cn(
                    "font-medium",
                    changes.new.length ? TONE_TEXT.error : "",
                  )}
                >
                  {changes.new.length} newly flagged
                </span>
                .
              </p>
            ) : null}
          </div>
        </SectionCard>
        <SectionCard title="Explore your audit" bodyClassName="py-1 px-3">
          <p className="px-2 pt-3 text-sm leading-6 text-text-secondary">
            See the current situation, supporting metrics and recommended next
            steps in each area.
          </p>
          <CategoryRings
            locationId={location.id}
            categories={health.categories}
          />
        </SectionCard>
      </div>
      {summary ? (
        <SectionCard
          title="What this audit tells you"
          actions={
            <span className="text-xs text-text-tertiary">
              {summary.source === "deterministic"
                ? "Written from the findings"
                : "AI summary · based on this audit’s findings"}
            </span>
          }
        >
          <p className="text-[15px] leading-7 text-text-primary">
            {summary.text}
          </p>
          {summary.strengths?.length || summary.attention?.length ? (
            <div className="mt-5 grid gap-4 border-t border-card-border pt-5 md:grid-cols-2">
              <InsightList
                title="Working well"
                tone="success"
                points={summary.strengths ?? []}
                labels={categoryLabels}
                locationId={location.id}
              />
              <InsightList
                title="Needs attention"
                tone="error"
                points={summary.attention ?? []}
                labels={categoryLabels}
                locationId={location.id}
              />
            </div>
          ) : null}
        </SectionCard>
      ) : null}

      {failedDrafts.length ? (
        <div
          className="rounded-xl border border-card-border bg-card-background px-5 py-4 text-sm leading-6"
          role="status"
        >
          <p className="font-medium text-badge-warning-text">
            Some AI drafts are unavailable
          </p>
          <p className="text-text-secondary">
            {failedDrafts
              .map(([category]) => categoryLabels.get(category) ?? category)
              .join(", ")}
            : the checks and recommendations are still available. Rerun the
            audit to try generating drafts again.
          </p>
        </div>
      ) : null}

      <SectionCard
        title="Your next steps"
        bodyClassName="px-0 py-0"
        actions={
          <Link
            href={sectionHref(location.id, "/issues")}
            className="inline-flex min-h-11 min-w-11 items-center text-sm text-text-secondary underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-primary-500"
          >
            View all findings
          </Link>
        }
      >
        <ol>
          {todo.map((item, index) => {
            const rule = byRule.get(item.rule);
            return (
              <li
                key={item.key}
                className="flex flex-wrap items-start gap-x-4 gap-y-2 border-b border-card-border px-5 py-4 last:border-b-0"
              >
                <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-background-gray-secondary text-sm font-semibold text-text-primary">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm leading-6 text-text-primary">
                    <Link
                      href={issueHref(location.id, item.rule)}
                      className="inline-flex min-h-11 items-center font-medium text-primary-500 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-primary-500"
                    >
                      {item.title}
                    </Link>
                  </p>
                  <p className="mt-0.5 text-sm leading-6 text-text-secondary">
                    {item.why}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-text-primary">
                    <span className="font-medium">Next step:</span>{" "}
                    {item.action}
                  </p>
                  <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-text-tertiary">
                    <Badge color={SEVERITY_COLOR[item.severity]} size="sm">
                      {item.severity}
                    </Badge>
                    {rule?.effort ? (
                      <span>
                        Estimated effort:{" "}
                        {EFFORT_LABEL[rule.effort] ?? rule.effort}
                      </span>
                    ) : null}
                    {item.suggestion ? (
                      <span className={TONE_TEXT.success}>
                        AI draft ready to review
                      </span>
                    ) : null}
                    {changes?.new.includes(item.rule) &&
                    !changes.first_audit ? (
                      <span className={TONE_TEXT.error}>
                        New since last audit
                      </span>
                    ) : null}
                  </p>
                </div>
              </li>
            );
          })}
          {!todo.length ? (
            <li className="px-5 py-8 text-sm text-text-secondary">
              {health.score === null
                ? "There is not enough evidence to recommend next steps. Open each area to see which checks could not be evaluated."
                : health.checks_failed > 0 || health.issues > 0
                  ? "No priorities were selected for this report. Open all findings to review the checks needing attention."
                  : health.checks_not_evaluated > 0
                    ? "Every evaluated check passed. Review the areas with missing evidence for a more complete picture."
                    : "Every evaluated check passed. Explore each area to review the supporting metrics."}
            </li>
          ) : null}
        </ol>
      </SectionCard>

      <p className="text-xs leading-5 text-text-tertiary">
        {health.basis}
        {health.score !== null ? (
          <>
            {" "}
            Overall grade:{" "}
            <span
              className={cn("font-medium", TONE_TEXT[scoreTone(health.score)])}
            >
              {health.grade}
            </span>
            .
          </>
        ) : null}
      </p>
    </div>
  );
}
