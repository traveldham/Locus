"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { useAuditRun } from "@/hooks/use-audit";
import type {
  AuditLocation,
  RecommendationRun,
} from "@/services/api/recommendations";
import Link from "next/link";
import { useParams } from "next/navigation";
import type { ReactNode } from "react";
import { AUDIT_ROOT, findLocation } from "./audit-nav";

/** Loading, error and never-run states, resolved once for every audit route. */
export function AuditGate({
  locationId,
  children,
}: {
  locationId: string;
  children: (run: RecommendationRun) => ReactNode;
}) {
  const { run, job, isAuditing, isPending, error, refetch } =
    useAuditRun(locationId);
  if (isPending) {
    return (
      <p role="status" className="text-text-secondary">
        Loading the audit…
      </p>
    );
  }
  if (error) {
    return (
      <ErrorState title="We could not load this audit" onRetry={refetch} />
    );
  }
  if (!run) {
    // A first audit already on its way is news, not an empty state.
    if (isAuditing) {
      return (
        <EmptyState
          title="Auditing this profile now"
          description={
            <>
              {job?.status === "pending"
                ? "Queued and waiting for a worker to pick it up."
                : `${job?.stage} · ${job?.progress}%`}{" "}
              The result appears here as soon as it finishes.
            </>
          }
        />
      );
    }
    return (
      <EmptyState
        title="This profile has not been audited yet"
        description="Run the first audit for this location, then its score and issues appear here."
      />
    );
  }
  return <>{children(run)}</>;
}

/** The same gate, narrowed to the one location the route is about. */
export function LocationScope({
  children,
}: {
  children: (run: RecommendationRun, location: AuditLocation) => ReactNode;
}) {
  const locationId = String(useParams().locationId ?? "");
  return (
    <AuditGate locationId={locationId}>
      {(run) => {
        const location = findLocation(run, locationId);
        if (!location) {
          return (
            <EmptyState
              title="This location is not in the selected audit"
              description={
                <>
                  It may have been added after this audit ran, or removed since.{" "}
                  <Link
                    href={AUDIT_ROOT}
                    className="underline underline-offset-4"
                  >
                    Pick another location
                  </Link>
                  .
                </>
              }
            />
          );
        }
        return <>{children(run, location)}</>;
      }}
    </AuditGate>
  );
}
