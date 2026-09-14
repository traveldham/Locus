"use client";

import type { CategoryScore } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import { TONE_FILL, TONE_TEXT, scoreTone } from "./audit-format";
import { sectionHref } from "./audit-nav";

const CATEGORY_CONTEXT: Record<string, string> = {
  profile: "Business details customers rely on",
  reputation: "Reviews and your response to customers",
  visibility: "Where you appear in local searches",
  operations: "Bookings and customer follow-through",
  performance: "Profile views and customer actions",
  content: "Photos, videos and business updates",
};

/** Comparable category scores, with evidence coverage separate from health. */
export function CategoryRings({
  locationId,
  categories,
}: {
  locationId: string;
  categories: CategoryScore[];
}) {
  return (
    <ul className="divide-y divide-card-border">
      {categories.map((row) => {
        const total =
          row.checks_passed + row.checks_failed + row.checks_not_evaluated;
        const tone = scoreTone(row.score);
        return (
          <li key={row.category}>
            <Link
              href={sectionHref(
                locationId,
                row.category === "profile"
                  ? "/profile"
                  : `/category/${row.category}`,
              )}
              className="group grid min-h-11 gap-3 rounded-lg px-2 py-4 motion-safe:transition-colors hover:bg-background-gray-secondary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500 sm:grid-cols-[minmax(0,1fr)_minmax(140px,0.75fr)] sm:items-center"
            >
              <span className="min-w-0">
                <span className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                  {row.label}
                  <svg
                    className="size-4 text-text-tertiary"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    aria-hidden="true"
                  >
                    <path d="m9 5 7 7-7 7" />
                  </svg>
                </span>
                <span className="mt-0.5 block text-xs leading-5 text-text-secondary">
                  {CATEGORY_CONTEXT[row.category]}
                </span>
                <span className="mt-1 block text-xs leading-5 text-text-secondary">
                  {total === 0
                    ? "No checks available"
                    : `${row.checks_passed} passed · ${row.checks_failed} need attention · ${row.checks_not_evaluated} not evaluated`}
                </span>
              </span>
              <span>
                <span className="mb-2 flex items-baseline justify-between gap-3">
                  <span className="text-xs text-text-secondary">
                    {row.weight}% category weight
                  </span>
                  <span
                    className={cn(
                      "shrink-0 text-sm font-semibold tabular-nums",
                      row.score === null
                        ? "text-text-secondary"
                        : TONE_TEXT[tone],
                    )}
                  >
                    {row.score === null ? "Not scored" : `${row.score}/100`}
                  </span>
                </span>
                <span
                  className="block h-2 overflow-hidden rounded-full bg-background-gray-secondary"
                  aria-hidden="true"
                >
                  <span
                    className={cn(
                      "block h-full rounded-full motion-safe:transition-[width] motion-safe:duration-500",
                      TONE_FILL[tone],
                    )}
                    style={{ width: `${row.score ?? 0}%` }}
                  />
                </span>
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
