import { SectionCard } from "@/components/common/section-card";
import type {
  AuditLocation,
  RuleCluster,
} from "@/services/api/recommendations";
import Link from "next/link";
import { issueHref } from "./audit-nav";

const PURPOSE: Record<string, string> = {
  profile:
    "Can customers find accurate business details and confidently choose your location?",
  reputation:
    "What do customer reviews say, and where does your team need to respond?",
  visibility:
    "Where does your location appear in tracked searches, and where is it missing?",
  operations:
    "Where do booking requests turn into appointments, and where do customers drop off?",
  performance:
    "How often is your profile seen, and what actions do customers take next?",
  content:
    "Do your photos and posts give customers a current, useful picture of your business?",
};

export function CategoryAuditHeader({
  category,
  label,
  location,
}: {
  category: string;
  label: string;
  location: AuditLocation;
}) {
  const score = location.health.categories.find(
    (entry) => entry.category === category,
  );
  const summary = location.summaries?.[category];
  const suggestions = location.suggestions?.[category];
  const evaluated = (score?.checks_passed ?? 0) + (score?.checks_failed ?? 0);
  const total = evaluated + (score?.checks_not_evaluated ?? 0);
  return (
    <section aria-label={`${label} summary`} className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <h2 className="text-xl font-semibold tracking-[-0.02em] text-text-primary">
            {label}
          </h2>
          <p className="mt-2 text-sm leading-6 text-text-secondary">
            {PURPOSE[category] ??
              "Review the saved evidence and the recommended next steps for this category."}
          </p>
        </div>
        <div className="text-sm text-text-secondary">
          <p className="font-medium text-text-primary">
            {score?.score == null
              ? "Not scored"
              : `${Math.round(score.score)}/100 category score`}
          </p>
          <p className="mt-1 tabular-nums">
            {evaluated} of {total} checks evaluated
          </p>
        </div>
      </div>
      {summary ? (
        <div className="border-t border-card-border pt-4">
          <p className="max-w-3xl text-[15px] leading-7 text-text-primary">
            {summary.text}
          </p>
          <p className="mt-2 text-xs leading-5 text-text-tertiary">
            {summary.model
              ? "AI interpretation of this audit’s evidence. Scores and check results are calculated separately."
              : "Summary of the recorded check results."}
          </p>
        </div>
      ) : null}
      {suggestions?.status === "failed" ? (
        <p className="rounded-lg bg-badge-warning-background px-4 py-3 text-sm leading-6 text-badge-warning-text">
          AI suggestions could not be created for this category. The recorded
          checks and recommendations below are still available. Rerun the audit
          to try generating drafts again.
        </p>
      ) : suggestions?.status === "skipped" ? (
        <p className="text-sm leading-6 text-text-secondary">
          AI suggestions were not generated for this category.{" "}
          {suggestions.reason === "Nothing to draft or summarise."
            ? "There was nothing to draft or summarise."
            : "Review the recorded checks and recommended actions below."}
        </p>
      ) : null}
    </section>
  );
}

export function CategoryChecks({
  checks,
  locationId,
}: {
  checks: RuleCluster[];
  locationId: string;
}) {
  const groups = [
    {
      label: "Needs attention",
      description: "Review the evidence and choose what to fix next.",
      tone: "text-badge-error-text",
      rows: checks.filter((r) => r.issues > 0 || r.state === "triggered"),
      open: true,
    },
    {
      label: "Passed",
      description:
        "These checks passed against the data available for this audit.",
      tone: "text-badge-success-text",
      rows: checks.filter((r) => r.issues === 0 && r.state === "clear"),
      open: false,
    },
    {
      label: "Not evaluated",
      description:
        "There is not enough evidence to judge these checks. This does not mean they passed.",
      tone: "text-text-secondary",
      rows: checks.filter(
        (r) =>
          r.issues === 0 &&
          (r.state === "insufficient_data" || r.state === null),
      ),
      open: false,
    },
    {
      label: "Not applicable",
      description: "These checks were excluded for the reasons shown below.",
      tone: "text-text-secondary",
      rows: checks.filter((r) => r.issues === 0 && r.state === "suppressed"),
      open: false,
    },
  ];
  return (
    <SectionCard title="What we checked" bodyClassName="p-0">
      <p className="border-b border-card-border px-5 py-4 text-sm leading-6 text-text-secondary">
        Every check is available here, including what passed and what needs more
        evidence. Open a group to see the reasons.
      </p>
      {!checks.length ? (
        <p className="px-5 py-6 text-sm text-text-secondary">
          No check results were saved for this category. Rerun the audit to
          evaluate the available data.
        </p>
      ) : (
        groups.map((group) => (
          <details
            key={group.label}
            open={group.open && group.rows.length > 0}
            className="group border-b border-card-border last:border-b-0"
          >
            <summary className="min-h-14 cursor-pointer px-5 py-4 text-sm font-medium text-text-primary transition-colors hover:bg-background-soft-100 focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-primary-500">
              <span className={group.tone}>{group.label}</span>
              <span className="ml-2 text-text-secondary tabular-nums">
                ({group.rows.length})
              </span>
            </summary>
            <div className="px-5 pb-3">
              <p className="mb-2 max-w-3xl text-sm leading-6 text-text-secondary">
                {group.rows.length
                  ? group.description
                  : `No checks in “${group.label.toLowerCase()}” for this audit.`}
              </p>
              <ul className="divide-y divide-card-border">
                {group.rows.map((rule) => (
                  <li
                    key={rule.rule}
                    className="flex flex-wrap items-start justify-between gap-x-5 gap-y-2 py-4"
                  >
                    <div className="min-w-0 flex-1 basis-64">
                      <h3 className="text-sm font-medium text-text-primary">
                        {rule.label}
                      </h3>
                      <p className="mt-1 max-w-3xl text-sm leading-6 text-text-secondary">
                        {rule.reason ||
                          rule.checks ||
                          "No explanation was saved for this check."}
                      </p>
                      {rule.issues > 0 && rule.fix ? (
                        <p className="mt-2 max-w-3xl text-sm leading-6 text-text-primary">
                          <span className="font-medium">Next step: </span>
                          {rule.fix}
                        </p>
                      ) : null}
                    </div>
                    {rule.issues > 0 ? (
                      <Link
                        href={issueHref(locationId, rule.rule)}
                        className="inline-flex min-h-11 min-w-11 items-center rounded-md px-2 text-sm font-medium text-primary-500 underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                        aria-label={`Review findings: ${rule.label}`}
                      >
                        Review{" "}
                        {rule.issues === 1
                          ? "finding"
                          : `${rule.issues} findings`}
                      </Link>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          </details>
        ))
      )}
    </SectionCard>
  );
}
