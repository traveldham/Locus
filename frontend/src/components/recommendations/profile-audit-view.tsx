"use client";

import type {
  AuditLocation,
  RecommendationRun,
} from "@/services/api/recommendations";
import { CategoryAuditView } from "./category-audit-view";

export function ProfileAuditView({
  run,
  location,
}: {
  run: RecommendationRun;
  location: AuditLocation;
}) {
  return <CategoryAuditView run={run} location={location} category="profile" />;
}
