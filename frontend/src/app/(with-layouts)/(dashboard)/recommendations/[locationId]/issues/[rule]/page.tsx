"use client";

import { LocationScope } from "@/components/recommendations/audit-states";
import { IssueDetail } from "@/components/recommendations/issue-detail";
import { useParams } from "next/navigation";

export default function IssueDetailPage() {
  const rule = String(useParams().rule ?? "");
  return (
    <LocationScope>
      {(run, location) => (
        <IssueDetail run={run} location={location} rule={rule} />
      )}
    </LocationScope>
  );
}
