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
                  className="text-xs text-text-tertiary underline-offset-4 hover:underline"
                >
                  {labels.get(point.category) ?? point.category}
                </Link>
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-text-tertiary">Nothing to list.</p>
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
  const draftStatus = location.suggestions?.profile;
  const categoryLabels = new Map(
    run.categories.map((c) => [c.category, c.label]),
  );

  return (
    <div className="space-y-5">
      {summary ? (
        <SectionCard
          title="In short"
          actions={
            <span className="text-xs text-text-tertiary">
              {summary.source === "deterministic"
                ? "Written from the findings"
                : `Written by ${summary.model} from all six audits`}
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
          {draftStatus?.status === "failed" ? (
            <p className="mt-3 text-xs leading-5 text-badge-warning-text">
              Drafts could not be generated this time: {draftStatus.error}
            </p>
          ) : null}
        </SectionCard>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <SectionCard title="Health score">
          <ScoreRing
            score={health.score}
            grade={health.grade}
            label={
              health.score === null
                ? "No category has checks that could run."
                : `${Math.round(health.coverage * 100)}% of checks had enough evidence to run.`
            }
          />
          <div className="mt-4 border-t border-card-border pt-4">
            <ScoreTrend history={history} />
          </div>
          {changes && !changes.first_audit ? (
            <p className="mt-3 text-xs leading-5 text-text-tertiary">
              Since the last audit:{" "}
              <span className={cn("font-medium", TONE_TEXT.success)}>
                {changes.fixed.length} fixed
              </span>
              {" · "}
              <span
                className={cn(
                  "font-medium",
                  changes.new.length ? TONE_TEXT.error : "",
                )}
              >
                {changes.new.length} new
              </span>
            </p>
          ) : null}
        </SectionCard>

        <SectionCard title="Scores by category">
          <CategoryRings
            locationId={location.id}
            categories={health.categories}
          />
        </SectionCard>
      </div>

      <SectionCard
        title="Do these first"
        bodyClassName="px-0 py-0"
        actions={
          <Link
            href={sectionHref(location.id, "/issues")}
            className="min-h-11 text-sm text-text-secondary underline underline-offset-4 focus-visible:outline-primary-500"
          >
            All issues
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
                      className="font-medium text-primary-500 underline-offset-4 hover:underline"
                    >
                      {item.title}
                    </Link>
                  </p>
                  <p className="mt-0.5 text-sm leading-6 text-text-secondary">
                    {item.why}
                  </p>
                  <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-text-tertiary">
                    <Badge color={SEVERITY_COLOR[item.severity]} size="sm">
                      {item.severity}
                    </Badge>
                    {rule?.effort ? (
                      <span>
                        Takes {EFFORT_LABEL[rule.effort] ?? rule.effort}
                      </span>
                    ) : null}
                    {item.suggestion ? (
                      <span className={TONE_TEXT.success}>Draft ready</span>
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
              Nothing to do. Every check that could run passed.
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
