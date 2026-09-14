"use client";

import styles from "@/components/locations/preview/google-profile.module.css";
import { Button } from "@/components/tailgrids/core/button";
import type {
  ProfileCard as ProfileCardData,
  Recommendation,
} from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import { useRouter } from "next/navigation";
import { storeDraft } from "./draft-handoff";

/** Which card element each profile check paints. */
const RULE_ELEMENT: Record<string, string> = {
  phone_missing: "phone",
  website_missing: "website",
  website_not_https: "website",
  address_incomplete: "address",
  pin_missing: "address",
  primary_category_missing: "category",
  secondary_categories_few: "category",
  category_attribute_mismatch: "category",
  services_without_category: "category",
  unverified: "verified",
  temporarily_closed: "status",
  opening_date_missing: "opened",
  opening_date_in_future: "opened",
  description_missing: "description",
  description_short: "description",
  description_too_long: "description",
  description_keyword_stuffed: "description",
  description_quality: "description",
  name_keyword_stuffed: "name",
  logo_missing: "logo",
  cover_photo_missing: "cover",
  hours_missing: "hours",
  hours_weekday_gaps: "hours",
  saturday_hours_inconsistent: "hours",
  hours_implausible: "hours",
  attributes_sparse: "attributes",
  accessibility_unanswered: "attributes",
  services_without_attribute: "attributes",
};

function flagged(items: Recommendation[]) {
  const map = new Map<string, Recommendation[]>();
  for (const item of items) {
    const element = RULE_ELEMENT[item.rule];
    if (!element) continue;
    map.set(element, [...(map.get(element) ?? []), item]);
  }
  return map;
}

/**
 * Which description draft wins when several rules each wrote one.
 *
 * Five checks may draft this one field, and they are not alternatives: a description can
 * be over the cap, keyword-stuffed and vague at the same time, and each rule drafts
 * against its own complaint alone. Severity cannot settle it — it ranks how much the
 * profile is hurt, not which rewrite supersedes which — so the order is the strictness of
 * the constraint each draft was written to satisfy. A draft that already fits the cap and
 * reads as plain language can still be expanded by hand; an expanded draft that breaks
 * the cap is one Google refuses to save at all, so the hard limits come first.
 */
const DESCRIPTION_RULE_ORDER = [
  "description_missing",
  "description_too_long",
  "description_keyword_stuffed",
  "description_quality",
  "description_short",
];

/** The one description draft to show, and how many were in the running. */
function descriptionDraft(items: Recommendation[] | undefined) {
  const drafted = (items ?? []).filter(
    (i) =>
      i.suggestion?.field === "description" &&
      typeof i.suggestion.value === "string",
  );
  const rank = (rule: string) => {
    const at = DESCRIPTION_RULE_ORDER.indexOf(rule);
    return at === -1 ? DESCRIPTION_RULE_ORDER.length : at;
  };
  // Sorting is stable, so drafts from rules the order does not name keep audit order.
  const ordered = [...drafted].sort((a, b) => rank(a.rule) - rank(b.rule));
  return { chosen: ordered[0] ?? null, total: ordered.length };
}

function textDraft(items: Recommendation[] | undefined, field: string) {
  return (
    items?.find(
      (i) =>
        i.suggestion &&
        i.suggestion.field === field &&
        typeof i.suggestion.value === "string",
    ) ?? null
  );
}

function draftText(item: Recommendation | null) {
  return typeof item?.suggestion?.value === "string"
    ? item.suggestion.value
    : null;
}

function afterList(
  items: Recommendation[] | undefined,
  field: string,
): string[] {
  const out: string[] = [];
  for (const i of items ?? []) {
    if (i.suggestion?.field === field && Array.isArray(i.suggestion.value))
      out.push(...i.suggestion.value);
  }
  return [...new Set(out)];
}

function afterAttributes(
  items: Recommendation[] | undefined,
): Record<string, boolean> {
  const out: Record<string, boolean> = {};
  for (const i of items ?? []) {
    if (
      i.suggestion?.field === "attributes" &&
      !Array.isArray(i.suggestion.value) &&
      typeof i.suggestion.value === "object"
    )
      Object.assign(out, i.suggestion.value);
  }
  return out;
}

/** The profile as a customer sees it, twice: as stored, and with the drafts filled in. */
export function ProfileBeforeAfter({
  card,
  items,
}: {
  card: ProfileCardData;
  items: Recommendation[];
}) {
  const flags = flagged(items);
  const hasDrafts = items.some((i) => i.suggestion);
  const draftAttributes = afterAttributes(flags.get("attributes"));
  const nameDraft = textDraft(flags.get("name"), "title");
  const description = descriptionDraft(flags.get("description"));
  const changed = new Set<string>();
  if (draftText(nameDraft) !== null) changed.add("name");
  if (draftText(description.chosen) !== null) changed.add("description");
  if (afterList(flags.get("category"), "additional_categories").length)
    changed.add("category");
  if (Object.keys(draftAttributes).length) changed.add("attributes");
  return (
    <div className="space-y-4">
      <p className="text-sm leading-6 text-text-secondary">
        {hasDrafts
          ? `${changed.size} profile ${changed.size === 1 ? "field has" : "fields have"} proposed edits. Blue labels identify drafted fields; remaining highlighted issues still need your attention.`
          : "No AI edits are available in this report. Use the checks below to review the recommended changes and add business details that only you can confirm."}
      </p>
      <div className={cn("grid gap-5", hasDrafts && "lg:grid-cols-2")}>
        <Card title="Current saved profile" card={card} flags={flags} />
        {hasDrafts ? (
          <Card
            title="Proposed profile preview"
            card={{
              ...card,
              name: draftText(nameDraft) ?? card.name,
              description: draftText(description.chosen) ?? card.description,
              additional_categories: [
                ...new Set([
                  ...card.additional_categories,
                  ...afterList(flags.get("category"), "additional_categories"),
                ]),
              ],
              attributes_yes: [
                ...new Set([
                  ...card.attributes_yes.filter(
                    (key) => draftAttributes[key] !== false,
                  ),
                  ...Object.entries(draftAttributes)
                    .filter(([, v]) => v)
                    .map(([k]) => k),
                ]),
              ],
              attributes_no: [
                ...new Set([
                  ...card.attributes_no.filter(
                    (key) => draftAttributes[key] !== true,
                  ),
                  ...Object.entries(draftAttributes)
                    .filter(([, v]) => !v)
                    .map(([k]) => k),
                ]),
              ],
            }}
            flags={new Map([...flags].filter(([key]) => !changed.has(key)))}
            changed={changed}
            after
          />
        ) : null}
      </div>
      {hasDrafts ? (
        <DraftActions
          nameDraft={nameDraft}
          description={description}
          hasCategoryDraft={changed.has("category")}
          hasAttributeDraft={changed.has("attributes")}
        />
      ) : null}
    </div>
  );
}

/**
 * The way out of the preview: each drafted field the editor can take, as its own button.
 *
 * Only the two fields `DraftHandoff` carries are offered. The editor prefills one field
 * per visit and clears the handoff on arrival, so drafted categories and attributes are
 * named as read-only rather than given a button that would drop them on the way.
 */
function DraftActions({
  nameDraft,
  description,
  hasCategoryDraft,
  hasAttributeDraft,
}: {
  nameDraft: Recommendation | null;
  description: { chosen: Recommendation | null; total: number };
  hasCategoryDraft: boolean;
  hasAttributeDraft: boolean;
}) {
  const router = useRouter();
  const aboutDraft = description.chosen;
  const name = draftText(nameDraft);
  const about = draftText(aboutDraft);
  if (name === null && about === null) return null;

  function open(
    item: Recommendation,
    field: "title" | "description",
    value: string,
  ) {
    storeDraft(item.location_id, {
      field,
      value,
      reason: item.suggestion?.reason ?? "",
    });
    router.push(`/locations/${encodeURIComponent(item.location_id)}?draft=1`);
  }

  return (
    <section
      aria-label="Use these drafts"
      className="rounded-xl bg-background-gray-secondary px-4 py-4"
    >
      <h3 className="text-sm font-medium text-text-primary">
        Take a draft into the editor
      </h3>
      <p className="mt-1 max-w-prose text-xs leading-5 text-text-secondary">
        Each button opens the profile editor with that one field prefilled. You
        still read it, change it and save it there; nothing above is published
        from this page.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        {nameDraft && name !== null ? (
          <Button
            type="button"
            size="xl"
            onPress={() => open(nameDraft, "title", name)}
          >
            Edit the business name with this draft
          </Button>
        ) : null}
        {aboutDraft && about !== null ? (
          <Button
            type="button"
            size="xl"
            onPress={() => open(aboutDraft, "description", about)}
          >
            Edit the description with this draft
          </Button>
        ) : null}
      </div>
      {aboutDraft && description.total > 1 ? (
        <p className="mt-3 text-xs leading-5 text-text-secondary">
          {description.total} checks each drafted a description. The one shown
          is from &ldquo;{aboutDraft.title}&rdquo;, chosen because it answers
          the strictest limit on the field; the rest are under their own
          findings below.
        </p>
      ) : null}
      {hasCategoryDraft || hasAttributeDraft ? (
        <p className="mt-2 text-xs leading-5 text-text-tertiary">
          The drafted{" "}
          {hasCategoryDraft && hasAttributeDraft
            ? "categories and attribute answers"
            : hasCategoryDraft
              ? "categories"
              : "attribute answers"}{" "}
          have no editor field to open yet. Read them in the preview and set
          them in your Business Profile.
        </p>
      ) : null}
    </section>
  );
}

function Card({
  title,
  card,
  flags,
  after = false,
  changed = new Set<string>(),
}: {
  title: string;
  card: ProfileCardData;
  flags: Map<string, Recommendation[]>;
  after?: boolean;
  changed?: Set<string>;
}) {
  const mark = (element: string) =>
    flags.has(element)
      ? "rounded-md outline outline-2 outline-offset-2 outline-[#d93025]"
      : "";
  const note = (element: string) =>
    changed.has(element) ? (
      <span className="ml-2 text-xs font-medium text-[#1967d2]">
        AI draft · review
      </span>
    ) : flags.has(element) ? (
      <span className="ml-2 text-xs font-medium text-[#d93025]">
        Needs attention
      </span>
    ) : null;
  const address = [
    ...card.address.lines,
    [card.address.locality, card.address.administrative_area]
      .filter(Boolean)
      .join(", "),
    card.address.postal_code,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <section
      aria-label={title}
      className={cn(
        styles.panel,
        "h-full min-w-0 overflow-hidden border border-card-border",
      )}
    >
      <div className="border-b border-[#dadce0] px-4 py-2 text-xs font-medium tracking-wide text-[#5f6368] uppercase">
        {title}
        {after ? (
          <span className="ml-2 normal-case tracking-normal text-[#1967d2]">
            drafts, not published
          </span>
        ) : null}
      </div>
      <div className={cn("relative h-24 bg-[#e8eaed]", mark("cover"))}>
        {card.has_cover === false || (!after && flags.has("cover")) ? (
          <span className="absolute inset-0 flex items-center justify-center text-xs text-[#5f6368]">
            No cover photo{note("cover")}
          </span>
        ) : (
          <span className="absolute inset-0 flex items-center justify-center text-xs text-[#5f6368]">
            {card.has_cover === true
              ? "Cover photo recorded · image not included in audit"
              : "Cover photo status unknown"}
          </span>
        )}
        <span
          className={cn(
            "absolute -bottom-5 left-4 flex size-12 items-center justify-center rounded-full border-2 border-white bg-white text-[10px] text-[#5f6368] shadow",
            mark("logo"),
          )}
        >
          {card.has_logo === false
            ? "no logo"
            : card.has_logo === true
              ? "logo saved"
              : "unknown"}
        </span>
      </div>
      <div className="px-4 pt-8 pb-4">
        <h3 className={cn("text-xl font-medium", mark("name"))}>
          {card.name ?? "Unnamed"}
          {note("name")}
        </h3>
        <p className={cn("mt-1 text-sm text-[#5f6368]", mark("category"))}>
          {card.primary_category ?? "No category"}
          {card.additional_categories.filter(Boolean).length
            ? ` · ${card.additional_categories.filter(Boolean).join(", ")}`
            : ""}
          {note("category")}
        </p>
        <p className={cn("mt-1 text-xs", mark("verified"))}>
          {card.verified === true ? (
            <span className="text-[#1e8e3e]">Verified</span>
          ) : card.verified === false ? (
            <span className="text-[#d93025]">Not verified</span>
          ) : (
            <span className="text-[#5f6368]">Verification unknown</span>
          )}
          {note("verified")}
          {card.open_status && card.open_status !== "open" ? (
            <span className={cn("ml-2 text-[#d93025]", mark("status"))}>
              {card.open_status.replaceAll("_", " ")}
              {note("status")}
            </span>
          ) : null}
        </p>

        <div className="mt-3 flex flex-wrap gap-2 text-sm">
          <span
            className={cn(
              "rounded-full border border-[#dadce0] px-3 py-1",
              card.website ? "text-[#1967d2]" : "text-[#5f6368] line-through",
              mark("website"),
            )}
          >
            Website{note("website")}
          </span>
          <span
            className={cn(
              "rounded-full border border-[#dadce0] px-3 py-1",
              card.address.locality
                ? "text-[#1967d2]"
                : "text-[#5f6368] line-through",
              mark("address"),
            )}
          >
            Directions{note("address")}
          </span>
          <span
            className={cn(
              "rounded-full border border-[#dadce0] px-3 py-1",
              card.phone ? "text-[#1967d2]" : "text-[#5f6368] line-through",
              mark("phone"),
            )}
          >
            Call{note("phone")}
          </span>
        </div>

        <dl className="mt-4 space-y-2 text-sm">
          <div className={cn("flex gap-3", mark("address"))}>
            <dt className="w-20 shrink-0 text-[#5f6368]">Address</dt>
            <dd className="min-w-0 break-words">{address || "Not set"}</dd>
          </div>
          <div className={cn("flex gap-3", mark("phone"))}>
            <dt className="w-20 shrink-0 text-[#5f6368]">Phone</dt>
            <dd className="min-w-0 break-words">{card.phone ?? "Not set"}</dd>
          </div>
          <div className={cn("flex gap-3", mark("website"))}>
            <dt className="w-20 shrink-0 text-[#5f6368]">Website</dt>
            <dd className="break-all">{card.website ?? "Not set"}</dd>
          </div>
          <div className={cn("flex gap-3", mark("hours"))}>
            <dt className="w-20 shrink-0 text-[#5f6368]">Hours</dt>
            <dd>
              {card.hours.length ? (
                <ul>
                  {card.hours.map((h) => (
                    <li key={h.day}>
                      {h.day} {h.open}–{h.close}
                    </li>
                  ))}
                </ul>
              ) : (
                "Hours unknown"
              )}
              {note("hours")}
            </dd>
          </div>
          <div className={cn("flex gap-3", mark("opened"))}>
            <dt className="w-20 shrink-0 text-[#5f6368]">Opened</dt>
            <dd>
              {card.opening_date ?? "Not set"}
              {note("opened")}
            </dd>
          </div>
        </dl>

        <div className={cn("mt-4", mark("description"))}>
          <h4 className="text-sm font-medium">About</h4>
          <p className="mt-1 text-sm leading-6 whitespace-pre-line">
            {card.description ?? "No description."}
            {note("description")}
          </p>
        </div>

        <div className={cn("mt-4", mark("attributes"))}>
          <h4 className="text-sm font-medium">
            Amenities and accessibility{note("attributes")}
          </h4>
          <p className="mt-1 text-sm leading-6 text-[#5f6368]">
            {card.attributes_yes.length
              ? card.attributes_yes
                  .map((a) => a.replaceAll("_", " "))
                  .join(" · ")
              : "Nothing confirmed yet."}
          </p>
          {card.attributes_no.length ? (
            <p className="mt-2 text-sm leading-6 text-[#5f6368]">
              Recorded as unavailable:{" "}
              {card.attributes_no
                .map((a) => a.replaceAll("_", " "))
                .join(" · ")}
            </p>
          ) : null}
        </div>
      </div>
    </section>
  );
}
