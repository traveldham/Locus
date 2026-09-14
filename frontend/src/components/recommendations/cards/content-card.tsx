"use client";

import { SectionCard } from "@/components/common/section-card";
import type { Recommendation } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import type { CategoryCardProps } from "./registry";

/** What the content worker's `card(snapshot)` returns. */
export interface ContentCardData {
  has_media_summary: boolean;
  photos: {
    total: number | null;
    interior: number | null;
    exterior: number | null;
    team: number | null;
    other: number | null;
    videos: number | null;
    last_uploaded_on: string | null;
    days_since_upload: number | null;
  };
  posts: {
    total: number;
    in_90_days: number;
    last_published_on: string | null;
    last_type: string | null;
    days_since_post: number | null;
    type_mix: Record<string, number>;
    cta_share: number | null;
    recent: {
      type: string;
      published_on: string;
      summary: string;
      cta: string | null;
    }[];
  };
}

const PHOTO_TYPES: {
  key: "interior" | "exterior" | "team" | "other";
  label: string;
}[] = [
  { key: "interior", label: "Interior" },
  { key: "exterior", label: "Exterior" },
  { key: "team", label: "Team" },
  { key: "other", label: "Other" },
];

const POST_TYPE_LABEL: Record<string, string> = {
  standard: "Update",
  event: "Event",
  offer: "Offer",
  alert: "Alert",
};

const CTA_LABEL: Record<string, string> = {
  book: "Book",
  call: "Call",
  learn_more: "Learn more",
  sign_up: "Sign up",
  get_offer: "Get offer",
};

/** Which card element each content check paints red. */
const RULE_ELEMENT: Record<string, string> = {
  photos_few: "photos",
  photos_below_target: "photos",
  photo_type_empty: "types",
  video_missing: "video",
  photos_stale: "upload",
  posts_none_recent: "last_post",
  posts_sparse: "cadence",
  post_types_uniform: "mix",
  posts_without_cta: "cta",
};

function isContentCard(value: unknown): value is ContentCardData {
  if (!value || typeof value !== "object") return false;
  const v = value as Record<string, unknown>;
  return typeof v.photos === "object" && typeof v.posts === "object";
}

function days(n: number | null, none = "Unknown") {
  if (n === null) return none;
  if (n === 0) return "Today";
  return n === 1 ? "1 day ago" : `${n} days ago`;
}

function drafts(items: Recommendation[], field: string) {
  return items.filter(
    (i) => i.suggestion?.field === field && Array.isArray(i.suggestion.value),
  );
}

export function ContentCard({ card, items }: CategoryCardProps) {
  if (!isContentCard(card)) return null;
  const flagged = new Set(
    items.map((i) => RULE_ELEMENT[i.rule]).filter((e): e is string => !!e),
  );
  const emptyTypes = new Set(
    items.filter((i) => i.rule === "photo_type_empty").map((i) => i.subject),
  );
  const postDrafts = drafts(items, "post_drafts");
  const shotLists = drafts(items, "photo_shot_list");
  const { photos, posts } = card;
  const maxPhotoCount = Math.max(
    1,
    ...PHOTO_TYPES.map(({ key }) => photos[key] ?? 0),
  );
  const mixEntries = Object.entries(posts.type_mix).sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-5">
      <SectionCard
        title="Photos and posts as customers see them"
        bodyClassName="px-5 py-5"
        actions={
          <span className="text-xs text-text-tertiary">
            Saved content · suggestions are shown separately
          </span>
        }
      >
        <p className="mb-5 max-w-prose text-sm leading-6 text-text-secondary">
          Help customers recognise the business and understand what you offer.
          Review photo coverage and publishing activity, then use the drafts
          below to prepare updates.
        </p>
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-text-primary">Photos</h3>
            {!card.has_media_summary ? (
              <p className="mt-2 text-sm text-text-secondary">
                No photo summary is stored, so photo checks could not run.
              </p>
            ) : (
              <>
                <div className="mt-3 grid grid-cols-3 gap-2">
                  <Tile
                    label="Photos"
                    value={photos.total ?? "Unknown"}
                    flagged={flagged.has("photos")}
                  />
                  <Tile
                    label="Videos"
                    value={photos.videos ?? "Unknown"}
                    flagged={flagged.has("video")}
                  />
                  <Tile
                    label="Last upload"
                    value={days(photos.days_since_upload)}
                    flagged={flagged.has("upload")}
                    small
                  />
                </div>
                <ul
                  className="mt-4 space-y-2"
                  aria-label="Photo coverage by type"
                >
                  {PHOTO_TYPES.map(({ key, label }) => {
                    const value = photos[key];
                    const bad = emptyTypes.has(key);
                    const share = value === null ? 0 : value / maxPhotoCount;
                    return (
                      <li key={key} className="flex items-center gap-3 text-sm">
                        <span
                          className={cn(
                            "w-16 shrink-0 text-text-secondary",
                            bad && "font-medium text-badge-error-text",
                          )}
                        >
                          {label}
                        </span>
                        <span
                          className={cn(
                            "h-2 flex-1 overflow-hidden rounded-full bg-background-gray-secondary",
                            bad && "outline outline-1 outline-badge-error-text",
                          )}
                          role="img"
                          aria-label={`${label}: ${value ?? "unknown"} photos`}
                        >
                          <span
                            className={cn(
                              "block h-full rounded-full",
                              bad ? "bg-badge-error-text" : "bg-primary-500",
                            )}
                            style={{ width: `${Math.round(share * 100)}%` }}
                          />
                        </span>
                        <span className="w-10 shrink-0 text-right tabular-nums text-text-primary">
                          {value ?? "—"}
                        </span>
                      </li>
                    );
                  })}
                </ul>
                <p className="mt-2 text-xs text-text-tertiary">
                  Bar lengths compare recorded counts. Other means photos with
                  no type recorded; these are not targets. Last recorded upload:{" "}
                  {photos.last_uploaded_on ?? "unknown"}.
                </p>
              </>
            )}
          </div>

          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-text-primary">Posts</h3>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <Tile
                label="Last post"
                value={days(posts.days_since_post, "Not recorded")}
                flagged={flagged.has("last_post")}
                small
              />
              <Tile
                label="In 90 days"
                value={posts.in_90_days}
                flagged={flagged.has("cadence")}
              />
              <Tile
                label="With button"
                value={
                  posts.cta_share === null
                    ? "Unknown"
                    : `${Math.round(posts.cta_share * 100)}%`
                }
                flagged={flagged.has("cta")}
              />
            </div>
            <div
              className={cn(
                "mt-3 flex flex-wrap items-center gap-1.5 text-xs",
                flagged.has("mix") &&
                  "rounded-md outline outline-1 outline-offset-2 outline-badge-error-text",
              )}
            >
              <span className="text-text-tertiary">Mix (6 months):</span>
              {mixEntries.length ? (
                mixEntries.map(([type, n]) => (
                  <span
                    key={type}
                    className="rounded-full bg-background-gray-secondary px-2 py-0.5 text-text-secondary"
                  >
                    {POST_TYPE_LABEL[type] ?? type} {n}
                  </span>
                ))
              ) : (
                <span className="text-text-secondary">no posts</span>
              )}
            </div>
            {posts.recent.length ? (
              <ol className="mt-4 space-y-3" aria-label="Most recent posts">
                {posts.recent.map((post, index) => (
                  <li
                    key={`${post.published_on}-${index}`}
                    className="flex gap-3 text-sm"
                  >
                    <span className="mt-1.5 size-2 shrink-0 rounded-full bg-text-disable" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs">
                        <span className="rounded-full bg-background-gray-secondary px-2 py-0.5 font-medium text-text-secondary">
                          {POST_TYPE_LABEL[post.type] ?? post.type}
                        </span>
                        <span className="text-text-tertiary">
                          {post.published_on}
                        </span>
                        <span
                          className={cn(
                            post.cta
                              ? "text-text-tertiary"
                              : "text-badge-warning-text",
                          )}
                        >
                          {post.cta
                            ? `Button: ${CTA_LABEL[post.cta] ?? post.cta}`
                            : "No button"}
                        </span>
                      </div>
                      <p className="mt-1 leading-5 break-words text-text-primary">
                        {post.summary || "(no text)"}
                      </p>
                    </div>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="mt-4 text-sm text-text-secondary">
                No posts are stored for this profile.
              </p>
            )}
          </div>
        </div>
      </SectionCard>

      {postDrafts.length || shotLists.length ? (
        <SectionCard
          title="Drafts"
          bodyClassName="px-5 py-5"
          actions={
            <span className="text-xs text-text-tertiary">
              Generated, not published. Review before use.
            </span>
          }
        >
          <div className="grid gap-6 lg:grid-cols-2">
            {postDrafts.map((item) => (
              <div key={item.key} className="min-w-0">
                <h3 className="text-sm font-semibold text-text-primary">
                  Post drafts to review
                </h3>
                <p className="mt-0.5 text-xs text-text-tertiary">
                  For: {item.title}
                </p>
                <ol className="mt-3 space-y-3">
                  {(item.suggestion?.value as string[]).map((draft, index) => (
                    <li
                      key={index}
                      className="rounded-lg border border-card-border bg-background-gray-secondary px-4 py-3 text-sm leading-6 break-words whitespace-pre-line text-text-primary"
                    >
                      {draft}
                    </li>
                  ))}
                </ol>
                {item.suggestion?.reason ? (
                  <p className="mt-2 text-xs text-text-tertiary">
                    {item.suggestion.reason}
                  </p>
                ) : null}
              </div>
            ))}
            {shotLists.map((item) => (
              <div key={item.key} className="min-w-0">
                <h3 className="text-sm font-semibold text-text-primary">
                  Shot list{item.subject ? `: ${item.subject} photos` : ""}
                </h3>
                <p className="mt-0.5 text-xs text-text-tertiary">
                  For: {item.title}
                </p>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-6 text-text-primary">
                  {(item.suggestion?.value as string[]).map((shot, index) => (
                    <li key={index} className="break-words">
                      {shot}
                    </li>
                  ))}
                </ul>
                {item.suggestion?.reason ? (
                  <p className="mt-2 text-xs text-text-tertiary">
                    {item.suggestion.reason}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}

function Tile({
  label,
  value,
  flagged,
  small = false,
}: {
  label: string;
  value: string | number;
  flagged: boolean;
  small?: boolean;
}) {
  return (
    <div
      className={cn(
        "min-w-0 border-b border-card-border px-1 py-3",
        flagged && "border-badge-error-text",
      )}
    >
      <p className="text-xs text-text-secondary">{label}</p>
      <p
        className={cn(
          "mt-1 break-words font-semibold tabular-nums text-text-primary",
          small ? "text-sm" : "text-lg",
        )}
      >
        {value}
      </p>
      {flagged ? (
        <p className="mt-1 text-xs text-badge-error-text">Needs attention</p>
      ) : null}
    </div>
  );
}
