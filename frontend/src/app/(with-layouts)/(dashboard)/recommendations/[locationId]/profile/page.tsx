"use client";

import { LocationScope } from "@/components/recommendations/audit-states";
import { ProfileAuditView } from "@/components/recommendations/profile-audit-view";

export default function LocationProfileAuditPage() {
  return (
    <LocationScope>
      {(run, location) => <ProfileAuditView run={run} location={location} />}
    </LocationScope>
  );
}
