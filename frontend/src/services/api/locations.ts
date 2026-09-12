import { apiRequest } from "./client";

export type LocationOpenStatus = "open" | "closed_temporarily" | "closed_permanently";

/**
 * Where a profile came from. `fixture` is the sample dataset the API serves while Google
 * has not approved Business Profile API access for this project, and it is labelled as
 * such everywhere it is shown.
 */
export type LocationSource = "google" | "fixture" | "manual";

export interface LocationSummary {
  id: string;
  title: string;
  /** Prebuilt single-line address from the API; null when Google holds no address. */
  address: string | null;
  primary_category_display: string | null;
  open_status: LocationOpenStatus | null;
  has_voice_of_merchant: boolean;
  has_pending_edits: boolean;
  has_google_updated: boolean;
  is_duplicate: boolean;
  source: LocationSource;
  store_code: string | null;
  last_synced_at: string | null;
}

export interface LocationCategory {
  category_name: string;
  display_name: string | null;
  is_primary: boolean;
}

export interface LocationHoursPeriod {
  hours_type: string;
  open_day: string;
  open_hour: number;
  open_minute: number;
  close_day: string;
  close_hour: number;
  close_minute: number;
}

export interface LocationAttribute {
  attribute_id: string;
  value_type: string;
  values: unknown[];
}

export interface AttributeCatalogItem {
  external_attribute_id: string;
  attribute_name: string;
  attribute_group: string;
  applies_to_category: string;
  value_type: string;
}

export interface AttributeCatalog {
  items: AttributeCatalogItem[];
  total: number;
}

export interface LocationDetail extends LocationSummary {
  google_location_name: string;
  google_resource_name: string | null;
  source_location_id: string | null;
  place_id: string | null;
  address_lines: string[] | null;
  locality: string | null;
  administrative_area: string | null;
  postal_code: string | null;
  region_code: string | null;
  latitude: number | null;
  longitude: number | null;
  phone_primary: string | null;
  website_uri: string | null;
  description: string | null;
  opening_date: string | null;
  maps_uri: string | null;
  new_review_uri: string | null;
  created_at: string | null;
  updated_at: string | null;
  categories: LocationCategory[];
  hours_periods: LocationHoursPeriod[];
  attributes: LocationAttribute[];
}

/**
 * An edit submitted for review. Every field is optional: only the ones present are
 * considered, and an explicit `null` clears the value on the Google profile.
 */
export interface LocationEditRequest {
  title?: string;
  phone_primary?: string | null;
  website_uri?: string | null;
  description?: string | null;
  open_status?: LocationOpenStatus;
  hours_periods?: LocationHoursPeriod[];
}

/** One before/after pair, already rendered as display strings by the API. */
/**
 * One before/after pair. Scalar fields arrive as strings, but structured ones — hours
 * periods, attributes — arrive as arrays of objects so the client can format them
 * legibly rather than showing raw JSON.
 */
export interface FieldChange {
  field: string;
  label: string;
  current: unknown;
  proposed: unknown;
}

/**
 * The result of dry-running an edit against Google. `changes` is the only diff the
 * product shows; the client never computes its own.
 */
export interface EditPreview {
  changes: FieldChange[];
  update_mask: string[];
  /** Keyed by the request field name, for example `title` or `website_uri`. */
  field_errors: Record<string, string>;
  valid: boolean;
}

export type ProfileActionStatus =
  | "pending"
  | "approved"
  | "executing"
  | "succeeded"
  | "failed";

/** One entry of the audit trail for a profile. */
export interface ProfileAction {
  id: string;
  action_type: string;
  status: ProfileActionStatus;
  payload: Record<string, unknown>;
  error: string | null;
  created_at: string;
  /** The person who submitted the action; null when the API does not identify one. */
  user: string | null;
}

/** The audit endpoint returns a bare array, newest first — not a paged envelope. */
export type ProfileActionList = ProfileAction[];

/** The API caps a page at 200 locations, so that is what the list surfaces request. */
export const LOCATIONS_MAX_PAGE_SIZE = 200;

export interface LocationListParams {
  /** Restrict the result to the locations that belong to one project. */
  projectId?: string;
  /** Server-side search across the location fields. */
  q?: string;
  /** Defaults to 50 on the API; hard capped at 200. */
  limit?: number;
  offset?: number;
}

function locationPath(id: string) {
  return `/locations/${encodeURIComponent(id)}`;
}

export const locationsApi = {
  list: ({ projectId, q, limit, offset }: LocationListParams = {}) => {
    const query = new URLSearchParams();
    if (projectId) query.set("project_id", projectId);
    if (q) query.set("q", q);
    if (limit !== undefined) query.set("limit", String(limit));
    if (offset !== undefined) query.set("offset", String(offset));
    const search = query.toString();
    return apiRequest<LocationSummary[]>(`/locations${search ? `?${search}` : ""}`);
  },
  get: (id: string) => apiRequest<LocationDetail>(locationPath(id)),
  attributeCatalog: () => apiRequest<AttributeCatalog>("/locations/attribute-catalog"),
  /**
   * Dry-runs the edit against Google. Nothing on the live listing changes, so this is
   * safe to call as often as the person editing wants to look at the diff.
   */
  previewEdit: (id: string, input: LocationEditRequest) =>
    apiRequest<EditPreview>(`${locationPath(id)}/edits/preview`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  /** Applies the edit to the live Google listing and records it in the audit trail. */
  applyEdit: (id: string, input: LocationEditRequest) =>
    apiRequest<ProfileAction>(`${locationPath(id)}/edits`, {
      method: "POST",
      body: JSON.stringify(input),
    }),
  listActions: (id: string) => apiRequest<ProfileActionList>(`${locationPath(id)}/actions`),
};
