"use client";

import { searchIntentLabel, type TrackedKeyword } from "@/services/api/market";
import { cn } from "@/utils/cn";
import { formatDate } from "@/utils/format-date";
import { RankBadge } from "./rank-badge";

interface KeywordGroup {
  intent: string;
  keywords: TrackedKeyword[];
}

/** Groups in the order the API first mentions each intent, so the list is stable. */
function groupByIntent(keywords: TrackedKeyword[]): KeywordGroup[] {
  const groups: KeywordGroup[] = [];
  for (const keyword of keywords) {
    const existing = groups.find((group) => group.intent === keyword.search_intent);
    if (existing) existing.keywords.push(keyword);
    else groups.push({ intent: keyword.search_intent, keywords: [keyword] });
  }
  return groups;
}

export interface KeywordListProps {
  keywords: TrackedKeyword[];
  selectedId: string | null;
  onSelect: (keywordId: string) => void;
  /** Off when an intent filter is active — one heading over one group is noise. */
  showGroupHeadings?: boolean;
}

export function KeywordList({
  keywords,
  selectedId,
  onSelect,
  showGroupHeadings = true,
}: KeywordListProps) {
  const groups = showGroupHeadings
    ? groupByIntent(keywords)
    : [{ intent: "", keywords }];

  return (
    <div className="flex flex-col gap-5">
      {groups.map((group) => (
        <div key={group.intent || "all"}>
          {group.intent ? (
            <h3 className="px-1 pb-2 text-xs leading-4 font-semibold tracking-[0.04em] text-text-tertiary uppercase">
              {searchIntentLabel(group.intent)}
            </h3>
          ) : null}
          <ul className="flex flex-col gap-1.5">
            {group.keywords.map((keyword) => {
              const isSelected = keyword.id === selectedId;
              const startedOn = formatDate(keyword.tracking_started_on);

              return (
                <li key={keyword.id}>
                  <button
                    type="button"
                    aria-current={isSelected ? "true" : undefined}
                    onClick={() => onSelect(keyword.id)}
                    className={cn(
                      "flex min-h-11 w-full items-center justify-between gap-3 rounded-lg border px-3 py-2 text-left transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
                      isSelected
                        ? "border-primary-500 bg-background-gray-secondary"
                        : "border-transparent hover:border-card-border hover:bg-background-gray-secondary",
                    )}
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm leading-5 font-medium text-text-primary">
                        {keyword.keyword}
                      </span>
                      <span className="mt-0.5 block truncate text-xs leading-4 text-text-tertiary">
                        {[
                          keyword.device,
                          startedOn ? `tracked since ${startedOn}` : null,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                      </span>
                    </span>
                    <RankBadge rank={keyword.latest_rank} className="shrink-0" />
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </div>
  );
}
