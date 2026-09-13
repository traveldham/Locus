"use client";

import { LocationScope } from "@/components/recommendations/audit-states";
import { CategoryAuditView } from "@/components/recommendations/category-audit-view";
import { useParams } from "next/navigation";

export default function CategoryAuditPage() {
  const category = String(useParams().category ?? "");
  return (
    <LocationScope>
      {(run, location) => (
        <CategoryAuditView run={run} location={location} category={category} />
      )}
    </LocationScope>
  );
}
