import { apiRequest } from "./client";

export interface Evidence {
  source: string;
  row_ids: string[];
  fields: string[];
  calculation: string;
  values: Record<string, unknown>;
}
export type Severity = "critical" | "warning" | "notice";
export type VerdictState =
  | "triggered"
  | "clear"
  | "insufficient_data"
  | "suppressed";
/** A generated draft for a field the audit found missing or weak. Reviewed by a
 *  person before anything is published; never a fact. */
export interface Suggestion {
  field: string;
  value: string | string[] | Record<string, boolean>;
  reason: string;
  confidence: "high" | "medium" | "low";
  source: string;
  model: string;
  generated_at: string;
}
export interface Recommendation {
  key: string;
  rule: string;
  subject: string;
  location_id: string;
  location_name: string;
  category: string;
  category_label: string;
  title: string;
  action: string;
  why: string;
  score: number;
  severity: Severity;
  confidence: "high" | "medium";
  confidence_reason: string;
  limitation: string;
  evidence: Evidence[];
  href: string;
  explanation_source: string;
  suggestion: Suggestion | null;
}
export interface CategoryScore {
  category: string;
  label: string;
  weight: number;
  score: number | null;
  checks_passed: number;
  checks_failed: number;
  checks_not_evaluated: number;
  issues: number;
  worst_severity: Severity | null;
}
export interface HealthScore {
  score: number | null;
  grade: "excellent" | "good" | "fair" | "poor" | "not_evaluated";
  coverage: number;
  checks_passed: number;
  checks_failed: number;
  checks_not_evaluated: number;
  issues: number;
  categories: CategoryScore[];
  basis: string;
}
/** One check as the audit reports it: whether it fired, passed or could not be judged. */
export interface RuleCluster {
  rule: string;
  category: string;
  category_label: string;
  /** What this check is, in one phrase — not one finding's title. */
  label: string;
  state: VerdictState | null;
  reason: string;
  /** `<count> <unit(s)> <predicate>` composes the one-line issue row. */
  unit: string;
  predicate: string;
  predicate_one: string;
  /** What the check counted — reviews, requests, keywords. Null when it simply passes
   *  or fails for the profile as a whole, with nothing countable behind it. */
  subject: string | null;
  subject_predicate: string | null;
  checks: string;
  fix: string;
  /** Which part of the category the check belongs to, for the completeness strip. */
  group?: string;
  /** How long the fix usually takes: minutes, hour, afternoon. */
  effort?: string;
  suggests?: string | null;
  issues: number;
  subjects_failed: number;
  subjects_examined: number;
  worst_severity: Severity | null;
  max_score: number;
  severity: Partial<Record<Severity, number>>;
}
/** The profile as a customer sees it, from the profile worker. */
export interface ProfileCard {
  name: string | null;
  primary_category: string | null;
  additional_categories: (string | null)[];
  phone: string | null;
  website: string | null;
  description: string | null;
  address: {
    lines: string[];
    locality: string | null;
    administrative_area: string | null;
    postal_code: string | null;
  };
  has_pin: boolean;
  hours: { day: string; open: string; close: string }[];
  verified: boolean | null;
  open_status: string | null;
  opening_date: string | null;
  has_logo: boolean | null;
  has_cover: boolean | null;
  photo_count: number | null;
  attributes_yes: string[];
  attributes_no: string[];
}
export interface AuditPoint {
  category: string;
  text: string;
}
export interface AuditSummary {
  text: string;
  /** Whole-audit summaries carry these; per-worker summaries do not. */
  strengths?: AuditPoint[];
  attention?: AuditPoint[];
  source: string;
  model: string | null;
  generated_at: string;
}
export interface AuditChanges {
  previous_audit_at: string | null;
  first_audit: boolean;
  fixed: string[];
  new: string[];
  previous_state: Record<string, VerdictState | null>;
}
export interface AuditLocation {
  id: string;
  name: string;
  source: string | null;
  source_location_id: string | null;
  count: number;
  health: HealthScore;
  /** Every check, not only the failing ones. */
  by_rule: RuleCluster[];
  /** Finding keys to do first: worst severity, draft ready, quickest. */
  priorities: string[];
  /** Per-worker visuals, keyed by category. Profile's is typed; others are their own shape. */
  cards: { profile?: ProfileCard } & Record<string, unknown>;
  /** Per-worker summaries, shown on each category tab. */
  summaries: Record<string, AuditSummary>;
  /** The whole-audit summary, shown on the Overview. */
  summary?: AuditSummary;
  suggestions: Record<
    string,
    { status: string; reason?: string; error?: string; model?: string }
  >;
  changes?: AuditChanges;
}
export interface ScorePoint {
  run_id: string;
  at: string;
  score: number | null;
  issues: number;
  coverage: number;
}
export interface RecommendationRun {
  id: string;
  location_id: string;
  created_at: string;
  as_of: string;
  engine_version: string;
  fingerprint: string;
  config: Record<string, number>;
  categories: { category: string; label: string; weight: number }[];
  location: AuditLocation;
  items: Recommendation[];
  evaluations: {
    location_id: string;
    rule: string;
    category: string;
    state: VerdictState;
    reason: string;
    issues: number;
    evaluated: number;
  }[];
  limitations: string[];
}
export type JobStatus = "pending" | "running" | "succeeded" | "failed";
/** One category's share of an audit, tracked on its own. */
export interface AuditWorker {
  category: string;
  label: string;
  status: JobStatus;
  stage: string;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
}
/** One audit of one profile: the pipeline the six workers run inside. */
export interface AuditJob {
  id: string;
  location_id: string;
  status: JobStatus;
  /** What the pipeline is doing right now, in words the dashboard shows directly. */
  stage: string;
  /** Share of workers finished. Says nothing about how complete the profile is. */
  progress: number;
  as_of: string;
  run_id: string | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  workers: AuditWorker[];
}
/** One row of the profile directory: each location carries its own audit. */
export interface DirectoryRow {
  location_id: string;
  name: string;
  source_location_id: string | null;
  audited_at: string | null;
  as_of: string | null;
  engine_version: string | null;
  score: number | null;
  grade: HealthScore["grade"] | null;
  coverage: number | null;
  issues: number | null;
  severity: Partial<Record<Severity, number>>;
  job: AuditJob | null;
}
export const recommendationApi = {
  overview: (projectId?: string | null) =>
    apiRequest<{ items: DirectoryRow[] }>(
      `/recommendations/overview${projectId ? `?project_id=${encodeURIComponent(projectId)}` : ""}`,
    ),
  latest: (locationId: string) =>
    apiRequest<{
      run: RecommendationRun | null;
      inputs_changed: boolean;
      /** Set while an audit is being generated. The run above stays readable. */
      job: AuditJob | null;
      /** Past audits' scores, oldest first. */
      history: ScorePoint[];
    }>(`/recommendations/latest?location_id=${encodeURIComponent(locationId)}`),
  generate: (locationId: string) =>
    apiRequest<AuditJob>("/recommendations/runs", {
      method: "POST",
      body: JSON.stringify({ location_id: locationId }),
    }),
  job: (id: string) => apiRequest<AuditJob>(`/recommendations/jobs/${id}`),
  evidence: (runId: string, key: string, source: string, offset: number) => {
    const params = new URLSearchParams({
      source,
      recommendation_key: key,
      offset: String(offset),
    });
    return apiRequest<{ items: Record<string, unknown>[]; total: number }>(
      `/recommendations/runs/${runId}/evidence?${params}`,
    );
  },
};
