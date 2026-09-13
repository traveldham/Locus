"use client";

import type { CategoryScore } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import { GRADE_LABEL, TONE_STROKE, TONE_TEXT, scoreTone } from "./audit-format";
import { sectionHref, withParam } from "./audit-nav";

function Ring({ score, size = 72 }: { score: number | null; size?: number }) {
  const tone = scoreTone(score);
  const stroke = 7;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const filled = score === null ? 0 : (score / 100) * circumference;
  return (
    <span
      className="relative inline-flex shrink-0"
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        aria-hidden="true"
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          className="stroke-card-border"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          className={cn(
            "transition-[stroke-dasharray] duration-500",
            TONE_STROKE[tone],
          )}
        />
      </svg>
      <span
        className={cn(
          "absolute inset-0 flex items-center justify-center text-lg font-semibold tracking-[-0.02em]",
          TONE_TEXT[tone],
        )}
      >
        {score ?? "—"}
      </span>
    </span>
  );
}

/** One box per category, each with its own ring. Click opens that category's issues. */
export function CategoryRings({
  locationId,
  categories,
}: {
  locationId: string;
  categories: CategoryScore[];
}) {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {categories.map((row) => {
        const evaluated = row.checks_passed + row.checks_failed;
        const total = evaluated + row.checks_not_evaluated;
        const grade =
          row.score === null
            ? "not_evaluated"
            : row.score >= 90
              ? "excellent"
              : row.score >= 75
                ? "good"
                : row.score >= 50
                  ? "fair"
                  : "poor";
        return (
          <li key={row.category}>
            <Link
              href={withParam(
                sectionHref(locationId, "/issues"),
                "area",
                row.category,
              )}
              aria-label={`${row.label}: ${row.score ?? "not evaluated"} out of 100. Open its issues.`}
              className="flex h-full items-center gap-4 rounded-xl border border-card-border bg-card-background px-4 py-4 transition hover:border-primary-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
            >
              <Ring score={row.score} />
              <span className="min-w-0">
                <span className="block text-sm font-semibold text-text-primary">
                  {row.label}
                  <span className="ml-1.5 text-xs font-normal text-text-tertiary">
                    {row.weight}%
                  </span>
                </span>
                <span
                  className={cn(
                    "block text-xs font-medium",
                    TONE_TEXT[scoreTone(row.score)],
                  )}
                >
                  {GRADE_LABEL[grade]}
                </span>
                <span className="mt-1 block text-xs leading-5 text-text-tertiary">
                  {total === 0
                    ? "No checks built yet"
                    : row.score === null
                      ? `${total} checks, none could run`
                      : `${row.issues} ${row.issues === 1 ? "issue" : "issues"} · ${evaluated} of ${total} checks ran`}
                </span>
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
