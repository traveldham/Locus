"use client";

import { SectionCard } from "@/components/common/section-card";
import type { Recommendation } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import { TONE_FILL, TONE_TEXT } from "../audit-format";
import type { CategoryCardProps } from "./registry";

/** What the operations worker's `card(snapshot)` returns. */
export interface OperationsCardData {
  as_of: string | null;
  window_days: number;
  requests: number;
  funnel: {
    new: number;
    confirmed: number;
    completed: number;
    cancelled: number;
    no_show: number;
  };
  confirmation_rate: number | null;
  cancellation_rate: number | null;
  no_show_rate: number | null;
  settled: number;
  median_lead_days: number | null;
  oldest_new_age_days: number | null;
  services: { service: string; requests: number }[];
  channels: { channel: string; requests: number }[];
  weekend_requests: number;
}

type Tone = keyof typeof TONE_TEXT;

const FUNNEL_STEPS: {
  key: keyof OperationsCardData["funnel"];
  label: string;
  fill: string;
}[] = [
  { key: "new", label: "Waiting", fill: "bg-text-disable" },
  { key: "confirmed", label: "Confirmed", fill: "bg-primary-500" },
  { key: "completed", label: "Completed", fill: "bg-badge-success-text" },
  { key: "cancelled", label: "Cancelled", fill: "bg-badge-warning-text" },
  { key: "no_show", label: "No-show", fill: "bg-badge-error-text" },
];

function pct(value: number | null): string {
  return value === null ? "—" : `${Math.round(value * 100)}%`;
}

function higherIsBetter(
  value: number | null,
  good: number,
  fair: number,
): Tone {
  if (value === null) return "muted";
  if (value >= good) return "success";
  if (value >= fair) return "warning";
  return "error";
}

function lowerIsBetter(value: number | null, good: number, fair: number): Tone {
  if (value === null) return "muted";
  if (value <= good) return "success";
  if (value <= fair) return "warning";
  return "error";
}

function isCardData(value: unknown): value is OperationsCardData {
  return (
    typeof value === "object" &&
    value !== null &&
    "funnel" in value &&
    "requests" in value
  );
}

function Tile({
  label,
  value,
  tone,
  hint,
}: {
  label: string;
  value: string;
  tone: Tone;
  hint: string;
}) {
  return (
    <div className="min-w-0 border-b border-card-border py-4">
      <p className="text-sm font-medium text-text-secondary">{label}</p>
      <p
        className={cn(
          "mt-1 text-2xl font-semibold tracking-[-0.02em]",
          TONE_TEXT[tone],
        )}
      >
        {value}
      </p>
      <p className="mt-0.5 text-xs text-text-secondary">{hint}</p>
    </div>
  );
}

function Bars({
  rows,
  ariaLabel,
}: {
  rows: { label: string; value: number; fill?: string }[];
  ariaLabel: string;
}) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <ul aria-label={ariaLabel} className="space-y-2">
      {rows.map((row) => (
        <li
          key={row.label}
          className="grid grid-cols-[minmax(5rem,1fr)_minmax(3rem,1.5fr)_2.5rem] items-center gap-2 text-sm"
        >
          <span className="break-words text-text-secondary">{row.label}</span>
          <span
            aria-hidden="true"
            className="h-2.5 overflow-hidden rounded-full bg-background-gray-secondary"
          >
            <span
              className={cn(
                "block h-full rounded-full",
                row.fill ?? TONE_FILL.muted,
              )}
              style={{ width: `${(row.value / max) * 100}%` }}
            />
          </span>
          <span className="text-right font-medium tabular-nums text-text-primary">
            {row.value}
          </span>
        </li>
      ))}
    </ul>
  );
}

/** The request funnel, its loss rates, and the demand shape, with any drafted follow-up. */
export function OperationsCard({ card, items }: CategoryCardProps) {
  if (!isCardData(card)) return null;
  const followups = items.filter(
    (i: Recommendation) =>
      i.suggestion?.field === "followup_message" &&
      typeof i.suggestion.value === "string",
  );
  const oldest = card.oldest_new_age_days;

  return (
    <SectionCard
      title="Appointment requests"
      bodyClassName="px-5 py-5"
      actions={
        <span className="text-xs text-text-tertiary">
          {card.requests} requests in the last {card.window_days} days
          {card.as_of ? ` to ${card.as_of}` : ""}
        </span>
      }
    >
      {card.requests === 0 ? (
        <p className="text-sm text-text-secondary">
          No booking requests in the window, so nothing here can be judged.
        </p>
      ) : (
        <div className="space-y-6">
          <p className="max-w-prose text-sm leading-6 text-text-secondary">
            See which appointment requests need a response and how recorded
            visits ended. These requests include all recorded channels, not only
            Google.
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <Tile
              label="Confirmed"
              value={pct(card.confirmation_rate)}
              tone={higherIsBetter(card.confirmation_rate, 0.7, 0.5)}
              hint="of decided requests"
            />
            <Tile
              label="Cancelled"
              value={pct(card.cancellation_rate)}
              tone={lowerIsBetter(card.cancellation_rate, 0.2, 0.3)}
              hint={`of ${card.settled} settled visits`}
            />
            <Tile
              label="No-show"
              value={pct(card.no_show_rate)}
              tone={lowerIsBetter(card.no_show_rate, 0.1, 0.2)}
              hint={`of ${card.settled} settled visits`}
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div>
              <h3 className="text-sm font-semibold text-text-primary">
                Where requests stand
              </h3>
              <p className="mt-1 text-xs leading-5 text-text-secondary">
                Each request appears in its current status once. These bars are
                a status breakdown, not steps in a conversion funnel.
              </p>
              <div className="mt-3">
                <Bars
                  ariaLabel="Requests by status"
                  rows={FUNNEL_STEPS.map((step) => ({
                    label: step.label,
                    value: card.funnel[step.key],
                    fill: step.fill,
                  }))}
                />
              </div>
              <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-text-tertiary">Median lead time</dt>
                  <dd className="font-medium text-text-primary">
                    {card.median_lead_days === null
                      ? "—"
                      : `${card.median_lead_days} days`}
                  </dd>
                </div>
                <div>
                  <dt className="text-text-tertiary">Oldest waiting request</dt>
                  <dd
                    className={cn(
                      "font-medium",
                      TONE_TEXT[lowerIsBetter(oldest, 3, 7)],
                    )}
                  >
                    {oldest === null ? "none waiting" : `${oldest} days`}
                  </dd>
                </div>
                <div>
                  <dt className="text-text-tertiary">Weekend requests</dt>
                  <dd className="font-medium text-text-primary">
                    {card.weekend_requests}
                  </dd>
                </div>
              </dl>
            </div>

            <div className="space-y-5">
              <div>
                <h3 className="text-sm font-medium text-text-primary">
                  Services requested
                </h3>
                <div className="mt-3">
                  {card.services.length ? (
                    <Bars
                      ariaLabel="Requests by service"
                      rows={card.services.map((s) => ({
                        label: s.service,
                        value: s.requests,
                        fill: TONE_FILL.success,
                      }))}
                    />
                  ) : (
                    <p className="text-sm text-text-secondary">
                      No request names a service.
                    </p>
                  )}
                </div>
              </div>
              <div>
                <h3 className="text-sm font-medium text-text-primary">
                  Where requests come from
                </h3>
                <div className="mt-3">
                  {card.channels.length ? (
                    <Bars
                      ariaLabel="Requests by channel"
                      rows={card.channels.map((c) => ({
                        label:
                          (
                            {
                              google_profile: "Google profile",
                              walk_in: "Walk-in",
                              website: "Website",
                              phone: "Phone",
                            } as Record<string, string>
                          )[c.channel] ?? c.channel,
                        value: c.requests,
                        fill: "bg-primary-500",
                      }))}
                    />
                  ) : (
                    <p className="text-sm text-text-secondary">
                      No request carries a channel.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
          <details className="border-t border-card-border pt-2 text-sm">
            <summary className="flex min-h-11 cursor-pointer items-center text-primary-500 focus-visible:outline-2 focus-visible:outline-primary-500">
              How these rates are calculated
            </summary>
            <p className="max-w-prose pb-3 leading-6 text-text-secondary">
              Confirmation counts confirmed, completed and no-show requests out
              of requests with a decision. Cancellation and no-show rates use
              only completed, cancelled and no-show visits. Waiting requests and
              future confirmed visits do not belong in that outcome total. Lead
              time measures the time from request creation to the requested
              appointment date.
            </p>
          </details>

          {followups.length ? (
            <div className="rounded-xl bg-background-gray-secondary px-4 py-4">
              <h3 className="text-sm font-medium text-text-primary">
                Drafted follow-up
                <span className="ml-1.5 font-normal text-text-tertiary">
                  · for request {followups[0].subject}, not sent
                </span>
              </h3>
              <p className="mt-2 text-sm leading-6 whitespace-pre-line text-text-primary">
                {String(followups[0].suggestion?.value)}
              </p>
              {followups.length > 1 ? (
                <p className="mt-2 text-xs text-text-tertiary">
                  {followups.length - 1} more drafted under the findings below.
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      )}
    </SectionCard>
  );
}
