"use client";

import { LocationScope } from "@/components/recommendations/audit-states";
import { IssuesList } from "@/components/recommendations/issues-list";

export default function LocationIssuesPage() {
  return (
    <LocationScope>
      {(run, location) => <IssuesList run={run} location={location} />}
    </LocationScope>
  );
}
