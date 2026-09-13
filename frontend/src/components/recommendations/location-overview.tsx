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
import { ProfileBeforeAfter } from "./profile-card";
import { ScoreRing } from "./score-ring";
import { ScoreTrend } from "./score-trend";

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
  const summary = location.summaries?.profile ?? null;
  const changes = location.changes;
  const byKey = new Map(run.items.map((item) => [item.key, item]));
  const byRule = new Map(location.by_rule.map((row) => [row.rule, row]));
  const todo = (location.priorities ?? [])
    .map((key) => byKey.get(key))
    .filter((item): item is NonNullable<typeof item> => Boolean(item));
  const card = location.cards?.profile;
  const profileItems = run.items.filter((item) => item.category === "profile");
  const draftStatus = location.suggestions?.profile;

  return (
    <div className="space-y-5">
      {summary ? (
        <SectionCard
          title="In short"
          actions={
            <span className="text-xs text-text-tertiary">
              {summary.source === "deterministic"
                ? "Written from the findings"
                : `Written by ${summary.model} from the findings`}
            </span>
          }
        >
          <p className="text-[15px] leading-7 text-text-primary">
            {summary.text}
          </p>
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

      {card ? (
        <SectionCard
          title="The profile, before and after"
          bodyClassName="px-5 py-5"
          actions={
            <span className="text-xs text-text-tertiary">
              Flagged elements are outlined in red
            </span>
          }
        >
          <ProfileBeforeAfter card={card} items={profileItems} />
        </SectionCard>
      ) : null}

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
