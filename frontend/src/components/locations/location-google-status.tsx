"use client";

import { SectionCard } from "@/components/common/section-card";
import type { LocationDetail } from "@/services/api/locations";
import { Shield1Check } from "@tailgrids/icons";
import { LocationStatusChip, type LocationStatusKind } from "./location-status-chip";

interface StatusRow {
  label: string;
  description: string;
  kind: LocationStatusKind;
}

function buildRows(location: LocationDetail): StatusRow[] {
  return [
    {
      label: "Voice of Merchant",
      description: "Whether Google recognises this profile as verified and managed by you.",
      kind: location.has_voice_of_merchant ? "verified" : "not_verified",
    },
    {
      label: "Pending edits",
      description: "Edits submitted to Google that have not been applied yet.",
      kind: location.has_pending_edits ? "pending_edits" : "no_pending_edits",
    },
    {
      label: "Google updates",
      description: "Changes Google has suggested for this profile.",
      kind: location.has_google_updated ? "google_updated" : "no_google_updates",
    },
    {
      label: "Duplicate",
      description: "Whether Google has flagged this profile as a duplicate listing.",
      kind: location.is_duplicate ? "duplicate" : "not_duplicate",
    },
  ];
}

export function LocationGoogleStatus({ location }: { location: LocationDetail }) {
  return (
    <SectionCard
      title="Google status"
      icon={<Shield1Check aria-hidden="true" focusable="false" />}
      bodyClassName="px-5 py-4"
    >
      <ul className="divide-y divide-card-border">
        {buildRows(location).map((row) => (
          <li key={row.label} className="py-3.5 first:pt-0 last:pb-0">
            <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
              <p className="text-sm font-medium text-text-primary">{row.label}</p>
              <LocationStatusChip kind={row.kind} />
            </div>
            <p className="mt-1 text-xs leading-5 text-text-tertiary">{row.description}</p>
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}
