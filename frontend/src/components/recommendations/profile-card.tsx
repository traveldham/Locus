"use client";

import styles from "@/components/locations/preview/google-profile.module.css";
import type {
  ProfileCard as ProfileCardData,
  Recommendation,
} from "@/services/api/recommendations";
import { cn } from "@/utils/cn";

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

function afterValue(items: Recommendation[] | undefined, field: string) {
  const with_ = items?.find(
    (i) =>
      i.suggestion &&
      i.suggestion.field === field &&
      typeof i.suggestion.value === "string",
  );
  return with_ ? String(with_.suggestion?.value) : null;
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
  const changed = new Set<string>();
  if (afterValue(flags.get("name"), "title") !== null) changed.add("name");
  if (afterValue(flags.get("description"), "description") !== null)
    changed.add("description");
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
              name: afterValue(flags.get("name"), "title") ?? card.name,
              description:
                afterValue(flags.get("description"), "description") ??
                card.description,
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
    </div>
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
