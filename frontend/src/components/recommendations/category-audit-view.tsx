"use client";

import { SectionCard } from "@/components/common/section-card";
import type {
  AuditLocation,
  RecommendationRun,
} from "@/services/api/recommendations";
import { CATEGORY_CARDS } from "./cards/registry";
import { ProfileBeforeAfter } from "./profile-card";
import { CategoryAuditHeader, CategoryChecks } from "./category-audit-sections";

export function CategoryAuditView({
  run,
  location,
  category,
}: {
  run: RecommendationRun;
  location: AuditLocation;
  category: string;
}) {
  const label =
    run.categories.find((c) => c.category === category)?.label ?? category;
  const items = run.items.filter((item) => item.category === category);
  const checks = location.by_rule.filter((rule) => rule.category === category);
  const card = location.cards?.[category];
  const Card = CATEGORY_CARDS[category];
  const profileCard =
    category === "profile" ? location.cards?.profile : undefined;

  return (
    <div className="space-y-7">
      <CategoryAuditHeader
        category={category}
        label={label}
        location={location}
      />
      {profileCard ? (
        <SectionCard
          title="Your profile: current details and proposed edits"
          bodyClassName="px-5 py-5"
        >
          <p className="mb-5 max-w-3xl text-sm leading-6 text-text-secondary">
            This preview uses the details saved with this audit. Highlighted
            fields need attention; AI drafts are suggestions for you to review
            before publishing.
          </p>
          <ProfileBeforeAfter card={profileCard} items={items} />
        </SectionCard>
      ) : card && Card ? (
        <Card card={card} items={items} location={location} />
      ) : (
        <p className="rounded-xl border border-card-border bg-card-background px-5 py-6 text-sm leading-6 text-text-secondary">
          This saved audit has no {label.toLowerCase()} preview.{" "}
          {checks.length
            ? "You can still review its checks below. Rerun the audit to refresh the report."
            : "Rerun the audit to check the available data for this category."}
        </p>
      )}
      <CategoryChecks checks={checks} locationId={location.id} />
    </div>
  );
}
