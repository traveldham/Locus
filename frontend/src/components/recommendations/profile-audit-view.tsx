"use client";

import { SectionCard } from "@/components/common/section-card";
import type {
  AuditLocation,
  RecommendationRun,
} from "@/services/api/recommendations";
import Link from "next/link";
import { issueHref } from "./audit-nav";
import { ProfileBeforeAfter } from "./profile-card";

export function ProfileAuditView({
  run,
  location,
}: {
  run: RecommendationRun;
  location: AuditLocation;
}) {
  const card = location.cards?.profile;
  const items = run.items.filter((item) => item.category === "profile");
  const checks = location.by_rule.filter((rule) => rule.category === "profile");
  const failing = checks.filter((rule) => rule.issues > 0);
  const passed = checks.filter((rule) => rule.state === "clear");
  const notEvaluated = checks.filter(
    (rule) => rule.state === "insufficient_data" || rule.state === "suppressed",
  );

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold tracking-[-0.02em] text-text-primary">
          Profile audit
        </h1>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-text-secondary">
          Compare the profile customers see today with the available AI drafts, then
          review each profile issue before making changes.
        </p>
      </div>

      {card ? (
        <SectionCard
          title="Current profile and suggested version"
          bodyClassName="px-5 py-5"
          actions={
            <span className="text-xs text-text-tertiary">
              Red outlines show fields that need attention
            </span>
          }
        >
          <ProfileBeforeAfter card={card} items={items} />
        </SectionCard>
      ) : (
        <p className="rounded-xl border border-card-border bg-card-background px-5 py-6 text-sm text-text-secondary">
          The saved audit does not contain a profile preview. Rerun the audit to create one.
        </p>
      )}

      <SectionCard title="Profile checks" bodyClassName="px-0 py-0">
        <div className="flex flex-wrap gap-x-5 gap-y-2 border-b border-card-border px-5 py-3 text-sm">
          <span className="font-medium text-badge-error-text">{failing.length} need attention</span>
          <span className="text-badge-success-text">{passed.length} passed</span>
          {notEvaluated.length ? (
            <span className="text-text-tertiary">{notEvaluated.length} not evaluated</span>
          ) : null}
        </div>
        <ul>
          {failing.map((rule) => (
            <li
              key={rule.rule}
              className="flex flex-wrap items-center gap-3 border-b border-card-border px-5 py-4 last:border-b-0"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text-primary">{rule.label}</p>
                <p className="mt-1 text-sm leading-6 text-text-secondary">{rule.reason}</p>
              </div>
              <Link
                href={issueHref(location.id, rule.rule)}
                className="inline-flex min-h-11 items-center text-sm font-medium text-primary-500 underline-offset-4 hover:underline focus-visible:outline-primary-500"
              >
                Understand and fix
              </Link>
            </li>
          ))}
          {!failing.length ? (
            <li className="px-5 py-8 text-sm text-text-secondary">
              Every profile check that could run passed.
            </li>
          ) : null}
        </ul>
      </SectionCard>
    </div>
  );
}
