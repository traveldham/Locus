"use client";

import type { RuleCluster } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import Link from "next/link";
import { useState } from "react";
import { TONE_TEXT } from "./audit-format";
import { issueHref } from "./audit-nav";

export function plural(n: number, noun: string) {
  return `${n.toLocaleString()} ${n === 1 ? noun : `${noun}s`}`;
}

/**
 * How a check reads in a single-profile audit.
 *
 * Where the check counted something — reviews, requests, keywords — the sentence is
 * about those. Where it simply passed or failed for the profile, saying "1 location has
 * X" is noise, so the finding's own wording is used instead.
 */
export function issueSentence(rule: RuleCluster, why?: string) {
  if (rule.subject && rule.subject_predicate) {
    const n = rule.subjects_failed || rule.issues;
    return {
      count: plural(n, rule.subject),
      predicate: rule.subject_predicate,
      detail: why,
      countable: true,
    };
  }
  // Nothing countable behind this check: its name leads and its own wording follows.
  return { count: rule.label, predicate: "", detail: why, countable: false };
}

export function IssueRow({
  rule,
  locationId,
  why,
}: {
  rule: RuleCluster;
  locationId: string;
  /** The finding's own wording, used where the check has nothing countable. */
  why?: string;
}) {
  const [open, setOpen] = useState(false);
  const sentence = issueSentence(rule, why);

  return (
    <li className="border-b border-card-border last:border-b-0">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 px-5 py-3.5">
        <p className="min-w-0 flex-1 text-sm leading-6 text-text-primary">
          <Link
            href={issueHref(locationId, rule.rule)}
            className="font-medium text-primary-500 underline-offset-4 hover:underline focus-visible:outline-primary-500"
          >
            {sentence.count}
          </Link>{" "}
          {sentence.predicate ? `${sentence.predicate} ` : ""}
          <button
            type="button"
            aria-expanded={open}
            onClick={() => setOpen(!open)}
            className="text-text-tertiary underline decoration-dotted underline-offset-4 hover:text-text-primary focus-visible:outline-primary-500"
          >
            How to fix
          </button>
        </p>
        {rule.new_issues ? (
          <Link
            href={issueHref(locationId, rule.rule)}
            className={cn("shrink-0 text-sm", TONE_TEXT.error)}
          >
            {rule.new_issues} new
          </Link>
        ) : (
          <span className="shrink-0 text-sm text-text-tertiary">no change</span>
        )}
      </div>
      {open ? (
        <div className="grid gap-4 border-t border-card-border bg-background-gray-secondary px-5 py-4 text-sm leading-6 sm:grid-cols-2">
          <div>
            <h3 className="font-medium text-text-primary">About this check</h3>
            <p className="mt-1 text-text-secondary">{rule.checks}</p>
          </div>
          <div>
            <h3 className="font-medium text-text-primary">How to fix</h3>
            <p className="mt-1 text-text-secondary">{rule.fix}</p>
          </div>
        </div>
      ) : null}
    </li>
  );
}
