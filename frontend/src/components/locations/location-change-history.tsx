"use client";

import { ErrorState } from "@/components/common/error-state";
import { SectionCard } from "@/components/common/section-card";
import { Skeleton } from "@/components/tailgrids/core/skeleton";
import { useLocationActionsQuery } from "@/hooks/use-locations";
import type { ProfileAction } from "@/services/api/locations";
import { formatDateTime } from "@/utils/format-date";
import { FileTextMultiple } from "@tailgrids/icons";
import { editFieldLabel } from "./edit-fields";
import { humanizeToken } from "./hours-model";
import { ProfileActionStatusChip } from "./profile-action-status-chip";

interface PayloadEntry {
  field: string;
  label: string;
  value: string | null;
}

function formatPayloadValue(field: string, value: unknown): string | null {
  if (value === null) return "Cleared";
  if (value === undefined) return null;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return "Cleared";
    return field === "open_status" ? humanizeToken(trimmed) : trimmed;
  }
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) {
    if (field === "hours") return value.length === 1 ? "1 period" : `${value.length} periods`;
    return value.length === 1 ? "1 entry" : `${value.length} entries`;
  }
  return null;
}

/**
 * The API decides what an action's payload holds. When it records an update mask
 * that is the authoritative list of fields; otherwise the payload's own keys are
 * shown, labelled as what was submitted rather than what changed.
 */
function summarisePayload(payload: Record<string, unknown>) {
  const rawMask = payload.update_mask;
  const mask = Array.isArray(rawMask)
    ? rawMask.filter((value): value is string => typeof value === "string")
    : null;

  const fields =
    mask && mask.length > 0
      ? mask
      : Object.keys(payload).filter((key) => key !== "update_mask");

  const entries: PayloadEntry[] = fields.map((field) => ({
    field,
    label: editFieldLabel(field),
    value: formatPayloadValue(field, payload[field]),
  }));

  return {
    caption: mask && mask.length > 0 ? "Fields updated" : "Fields submitted",
    entries,
  };
}

export function LocationChangeHistory({ locationId }: { locationId: string }) {
  const { data, isPending, isError, refetch, isFetching } = useLocationActionsQuery(locationId);
  const actions = data ?? [];

  return (
    <SectionCard
      title="Change history"
      icon={<FileTextMultiple aria-hidden="true" focusable="false" />}
      actions={
        actions.length > 0 ? (
          <span className="text-xs text-text-tertiary tabular-nums">
            {actions.length === 1 ? "1 action" : `${actions.length} actions`}
          </span>
        ) : null
      }
      bodyClassName="px-5 py-4"
    >
      {isPending ? <HistorySkeleton /> : null}

      {!isPending && isError ? (
        <ErrorState
          title="We could not load the change history"
          description="The audit trail for this profile did not load. Check your connection, then try again."
          onRetry={() => void refetch()}
          isRetrying={isFetching}
        />
      ) : null}

      {!isPending && !isError && actions.length === 0 ? (
        <p className="text-sm leading-6 text-text-tertiary">
          No changes have been sent to Google from Locus for this profile yet.
        </p>
      ) : null}

      {!isPending && !isError && actions.length > 0 ? (
        <ul className="divide-y divide-card-border">
          {actions.map((action) => (
            <HistoryRow key={action.id} action={action} />
          ))}
        </ul>
      ) : null}
    </SectionCard>
  );
}

function HistoryRow({ action }: { action: ProfileAction }) {
  const { caption, entries } = summarisePayload(action.payload);
  const timestamp = formatDateTime(action.created_at);

  return (
    <li className="py-3.5 first:pt-0 last:pb-0">
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <div className="min-w-0">
          <p className="text-sm font-medium text-text-primary">
            {humanizeToken(action.action_type)}
          </p>
          <p className="mt-0.5 text-xs leading-5 text-text-tertiary">
            {timestamp ?? "Time not recorded"}
            {action.user ? ` · ${action.user}` : ""}
          </p>
        </div>
        <ProfileActionStatusChip status={action.status} />
      </div>

      {entries.length > 0 ? (
        <>
          <p className="mt-2.5 text-[11px] font-medium tracking-[0.08em] text-text-tertiary uppercase">
            {caption}
          </p>
          <dl className="mt-1.5 grid gap-x-6 gap-y-1 sm:grid-cols-2">
            {entries.map((entry) => (
              <div key={entry.field} className="flex min-w-0 flex-wrap gap-x-2 text-sm leading-6">
                <dt className="shrink-0 text-text-tertiary">{entry.label}</dt>
                <dd className="min-w-0 flex-1 line-clamp-2 break-words text-text-secondary">
                  {entry.value ?? "—"}
                </dd>
              </div>
            ))}
          </dl>
        </>
      ) : null}

      {action.status === "failed" && action.error ? (
        <p className="mt-2.5 rounded-lg bg-alert-danger-background px-3 py-2 text-sm leading-5 text-alert-danger-description">
          {action.error}
        </p>
      ) : null}
    </li>
  );
}

function HistorySkeleton() {
  return (
    <div role="status" aria-label="Loading change history">
      {[0, 1].map((index) => (
        <div key={index} className="py-3.5 first:pt-0">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <Skeleton className="h-3.5 w-32" />
              <Skeleton className="mt-2 h-2.5 w-48 max-w-full" />
            </div>
            <Skeleton className="h-6 w-20 rounded-full" />
          </div>
          <Skeleton className="mt-3 h-3 w-56 max-w-full" />
        </div>
      ))}
    </div>
  );
}
