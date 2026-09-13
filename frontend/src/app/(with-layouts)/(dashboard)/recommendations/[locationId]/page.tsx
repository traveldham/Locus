"use client";

import { LocationScope } from "@/components/recommendations/audit-states";
import { LocationOverview } from "@/components/recommendations/location-overview";
import { useAuditRun } from "@/hooks/use-audit";
import { useParams } from "next/navigation";

export default function LocationAuditPage() {
  const locationId = String(useParams().locationId ?? "");
  const { history } = useAuditRun(locationId);
  return (
    <LocationScope>
      {(run, location) => (
        <LocationOverview run={run} location={location} history={history} />
      )}
    </LocationScope>
  );
}
