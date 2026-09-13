import type {
  AuditLocation,
  RecommendationRun,
} from "@/services/api/recommendations";

export const AUDIT_ROOT = "/recommendations";

/** Sections of a single location's audit. */
export const AUDIT_SECTIONS = [
  { href: "", label: "Overview" },
  { href: "/profile", label: "Profile" },
  { href: "/category/reputation", label: "Reputation" },
  { href: "/category/visibility", label: "Visibility" },
  { href: "/category/operations", label: "Operations" },
  { href: "/category/performance", label: "Performance" },
  { href: "/category/content", label: "Content" },
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

/** Tab badges count failing checks on both tabs, so the two numbers compare. */
export function sectionCounts(location: AuditLocation | undefined) {
  if (!location) return {};
  const failing = location.by_rule.filter((rule) => rule.issues > 0);
  const per = (category: string) =>
    failing.filter((rule) => rule.category === category).length;
  return {
    "/profile": per("profile"),
    "/category/reputation": per("reputation"),
    "/category/visibility": per("visibility"),
    "/category/operations": per("operations"),
    "/category/performance": per("performance"),
    "/category/content": per("content"),
    "/issues": failing.length,
  };
}

/** The run's one location, if it is the one the route is about. */
export function findLocation(
  run: RecommendationRun | null | undefined,
  locationId: string,
) {
  return run && run.location.id === locationId ? run.location : undefined;
}
