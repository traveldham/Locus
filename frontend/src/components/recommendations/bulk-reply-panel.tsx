"use client";

import { Badge } from "@/components/tailgrids/core/badge";
import { Button } from "@/components/tailgrids/core/button";
import { Checkbox } from "@/components/tailgrids/core/checkbox";
import { auditLatestKey } from "@/hooks/use-recommendations";
import {
  useBulkReplyToReviewsMutation,
  type BulkReplyResult,
} from "@/hooks/use-reviews";
import type { Recommendation } from "@/services/api/recommendations";
import { useQueryClient } from "@tanstack/react-query";
import { useMemo, useRef, useState } from "react";
import {
  replyDraftText,
  replySendErrorMessage,
  replyTargetId,
} from "./suggestion-panel";

/** One finding that can actually be published: a review to answer and a draft to send. */
interface ReplyRow {
  key: string;
  reviewId: string;
  comment: string;
  title: string;
  why: string;
}

/**
 * The findings this control may publish.
 *
 * Deliberately narrow. Most suggestion fields — themes, keyword plans, shot lists, post
 * drafts — have no write path at all, so eligibility is decided by what can be sent, not
 * by the rule name: a review row id from the finding's evidence, and a draft short enough
 * for Google to accept. `replyTargetId` is the only way to that id; the finding's subject
 * is Google's review id and the reply endpoint refuses it.
 *
 * Two findings naming the same review would publish twice over the same reply, so the
 * later one is dropped rather than queued.
 */
function eligibleRows(items: Recommendation[]): ReplyRow[] {
  const rows: ReplyRow[] = [];
  const seen = new Set<string>();
  for (const item of items) {
    const reviewId = replyTargetId(item);
    const comment = replyDraftText(item.suggestion);
    if (!reviewId || !comment || seen.has(reviewId)) continue;
    seen.add(reviewId);
    rows.push({
      key: item.key,
      reviewId,
      comment,
      title: item.title,
      why: item.why,
    });
  }
  return rows;
}

/**
 * Sends the drafted replies for a list of findings in one pass.
 *
 * Nothing is sent from the collapsed state: opening the list is what puts every draft in
 * front of the person before they can publish any of it.
 */
export function BulkReplyPanel({
  items,
  locationId,
}: {
  items: Recommendation[];
  locationId: string;
}) {
  const client = useQueryClient();
  const bulk = useBulkReplyToReviewsMutation();
  const rows = useMemo(() => eligibleRows(items), [items]);

  const [open, setOpen] = useState(false);
  // Deselection is what the user does, so it is what is stored: rows that appear after a
  // refetch start selected rather than silently excluded.
  const [excluded, setExcluded] = useState<ReadonlySet<string>>(new Set());
  const [results, setResults] = useState<Record<string, BulkReplyResult>>({});
  /** The keys of the most recent run, so its counts survive a later partial retry. */
  const [attempted, setAttempted] = useState<string[]>([]);
  const [stopped, setStopped] = useState(false);
  const [stopRequested, setStopRequested] = useState(false);
  const abort = useRef<AbortController | null>(null);

  const running = bulk.isPending;
  const sentKeys = new Set(
    Object.values(results)
      .filter((result) => !result.error)
      .map((result) => result.key),
  );
  // A sent reply leaves the queue entirely: a retry after a partial run must not publish
  // over a reply that already went out.
  const pending = rows.filter((row) => !sentKeys.has(row.key));
  const selected = pending.filter((row) => !excluded.has(row.key));
  const done = attempted.filter((key) => results[key]);
  const doneSent = done.filter((key) => !results[key].error);
  const doneFailed = done.filter((key) => results[key].error);
  const failedRows = rows.filter((row) => results[row.key]?.error);
  const finished = attempted.length > 0 && !running;

  if (rows.length < 2) return null;

  function toggle(key: string, include: boolean) {
    setExcluded((previous) => {
      const next = new Set(previous);
      if (include) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function send() {
    const queue = selected;
    if (!queue.length || running) return;
    const controller = new AbortController();
    abort.current = controller;
    setStopped(false);
    setStopRequested(false);
    setAttempted(queue.map((row) => row.key));
    // A row being tried again must not still be showing why it failed last time.
    setResults((previous) => {
      const next = { ...previous };
      for (const row of queue) delete next[row.key];
      return next;
    });
    bulk.mutate(
      {
        targets: queue.map((row) => ({
          key: row.key,
          id: row.reviewId,
          comment: row.comment,
        })),
        signal: controller.signal,
        onResult: (result) =>
          setResults((previous) => ({ ...previous, [result.key]: result })),
      },
      {
        onSuccess: (report) => {
          setStopped(report.stopped);
          // The reviews cache is refreshed by the mutation. This audit is a stored run
          // that still calls every one of these unanswered, but its `inputs_changed`
          // check reads live rows, so refetching it is what surfaces the new state.
          void client.invalidateQueries({
            queryKey: auditLatestKey(locationId),
          });
        },
      },
    );
  }

  function stop() {
    setStopRequested(true);
    abort.current?.abort();
  }

  const progressPct = attempted.length
    ? Math.round((done.length / attempted.length) * 100)
    : 0;

  return (
    <section
      aria-label="Send drafted replies together"
      className="rounded-xl border border-card-border bg-card-background px-5 py-4"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-text-primary">
            {rows.length} of these findings have a drafted reply
          </h2>
          <p className="mt-1 max-w-prose text-sm leading-6 text-text-secondary">
            Send them in one pass instead of opening each finding. Every reply
            is published publicly on Google under your business name, one after
            another, exactly as written.
          </p>
        </div>
        {!open ? (
          <Button type="button" size="xl" onPress={() => setOpen(true)}>
            Review {rows.length} drafts
          </Button>
        ) : (
          <Button
            type="button"
            size="xl"
            appearance="outline"
            onPress={() => setOpen(false)}
            isDisabled={running}
          >
            Close list
          </Button>
        )}
      </div>

      {open ? (
        <div className="mt-4 border-t border-card-border pt-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm text-text-secondary">
              {selected.length} of {pending.length} selected
            </span>
            <Button
              type="button"
              size="xl"
              appearance="ghost"
              onPress={() => setExcluded(new Set())}
              isDisabled={running || selected.length === pending.length}
            >
              Select all
            </Button>
            <Button
              type="button"
              size="xl"
              appearance="ghost"
              onPress={() =>
                setExcluded(new Set(pending.map((row) => row.key)))
              }
              isDisabled={running || selected.length === 0}
            >
              Clear selection
            </Button>
            <span className="grow" />
            {running ? (
              <Button
                type="button"
                size="xl"
                variant="danger"
                appearance="outline"
                onPress={stop}
                isDisabled={stopRequested}
              >
                {stopRequested ? "Stopping…" : "Stop"}
              </Button>
            ) : (
              <Button
                type="button"
                size="xl"
                onPress={send}
                isDisabled={selected.length === 0}
              >
                {failedRows.length && selected.length === failedRows.length
                  ? `Retry ${selected.length} failed`
                  : `Send ${selected.length} ${selected.length === 1 ? "reply" : "replies"} to Google`}
              </Button>
            )}
          </div>

          {running ? (
            <div className="mt-4">
              <div
                className="flex h-2 overflow-hidden rounded-full bg-background-gray-secondary"
                role="presentation"
              >
                <div
                  className="bg-primary-500 motion-safe:transition-[width] motion-safe:duration-300"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <p
                role="status"
                className="mt-2 text-sm leading-6 text-text-secondary"
              >
                {doneSent.length} of {attempted.length} sent
                {doneFailed.length
                  ? ` · ${doneFailed.length} failed so far`
                  : ""}
                {stopRequested
                  ? " · stopping once the reply in flight finishes"
                  : ""}
              </p>
            </div>
          ) : null}

          {finished ? (
            <div
              role="status"
              className="mt-4 rounded-lg bg-background-gray-secondary px-4 py-3 text-sm leading-6 text-text-primary"
            >
              <p>
                {doneSent.length} sent
                {doneFailed.length ? `, ${doneFailed.length} failed` : ""}
                {stopped
                  ? `. Stopped with ${attempted.length - done.length} not attempted — nothing was sent for those.`
                  : "."}
              </p>
              <p className="mt-1 text-text-secondary">
                {doneSent.length
                  ? "Sent replies are live on Google. These findings clear on the next audit."
                  : "Nothing was published."}
                {doneFailed.length
                  ? " The failed drafts are still selected below and can be sent again."
                  : ""}
              </p>
            </div>
          ) : null}

          <ul className="mt-4 divide-y divide-card-border">
            {rows.map((row) => {
              const result = results[row.key];
              const sent = Boolean(result) && !result.error;
              return (
                <li key={row.key} className="flex gap-3 py-3">
                  <Checkbox
                    isSelected={!sent && !excluded.has(row.key)}
                    onChange={(include) => toggle(row.key, include)}
                    isDisabled={running || sent}
                    aria-label={`Send the drafted reply to: ${row.title}`}
                    className="min-h-11 min-w-11 shrink-0 justify-center"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-sm font-medium text-text-primary">
                        {row.title}
                      </h3>
                      {sent ? (
                        <Badge color="success" size="sm">
                          sent
                        </Badge>
                      ) : result?.error ? (
                        <Badge color="error" size="sm">
                          failed
                        </Badge>
                      ) : null}
                    </div>
                    <p className="mt-1 text-xs leading-5 text-text-tertiary">
                      {row.why}
                    </p>
                    <p className="mt-2 rounded-md bg-background-gray-secondary px-3 py-2 text-sm leading-6 whitespace-pre-line text-text-primary">
                      {row.comment}
                    </p>
                    {result?.error ? (
                      <p className="mt-2 text-xs leading-5 text-badge-error-text">
                        {replySendErrorMessage(result.error)}
                      </p>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
          <p className="mt-3 text-xs leading-5 text-text-tertiary">
            AI drafts · read each one before sending. Deselect anything you do
            not want published.
          </p>
        </div>
      ) : null}
    </section>
  );
}
