import type {
  AuditLocation,
  RecommendationRun,
} from "@/services/api/recommendations";

export const AUDIT_ROOT = "/recommendations";

/** Sections of a single location's audit. */
export const AUDIT_SECTIONS = [
  { href: "", label: "Overview" },
  { href: "/profile", label: "Profile" },
  { href: "/issues", label: "Issues" },
] as const;

export function locationRoot(locationId: string) {
  return `${AUDIT_ROOT}/${encodeURIComponent(locationId)}`;
}

export function sectionHref(locationId: string, href: string) {
  return `${locationRoot(locationId)}${href}`;
}

export function issueHref(locationId: string, rule: string) {
  return sectionHref(locationId, `/issues/${rule}`);
}

export function withParam(href: string, key: string, value: string) {
  return `${href}${href.includes("?") ? "&" : "?"}${key}=${encodeURIComponent(value)}`;
}

export function sectionCounts(location: AuditLocation | undefined) {
  return location
    ? {
        "/profile": location.by_rule.filter(
          (rule) => rule.category === "profile" && rule.issues > 0,
        ).length,
        "/issues": location.count,
      }
    : {};
}

/** The run's one location, if it is the one the route is about. */
export function findLocation(
  run: RecommendationRun | null | undefined,
  locationId: string,
) {
  return run && run.location.id === locationId ? run.location : undefined;
}
