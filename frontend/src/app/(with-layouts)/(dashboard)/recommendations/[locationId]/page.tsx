"use client";

import { LocationScope } from "@/components/recommendations/audit-states";
import { LocationOverview } from "@/components/recommendations/location-overview";

export default function LocationAuditPage() {
  return (
    <LocationScope>
      {(_run, location) => <LocationOverview location={location} />}
    </LocationScope>
  );
}
