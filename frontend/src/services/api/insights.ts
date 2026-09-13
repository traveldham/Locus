import { apiRequest } from "./client";

/** Where a figure came from: Google's own reporting, or data Locus holds itself. */
export type DataSource = "google" | "locus";

/**
 * One day of Google performance reporting.
 *
 * Every metric is nullable and `null` is **not** zero: it means Google reported no
 * value for that day. Surfaces must render an absence, never a zero.
 */
export interface PerformancePoint {
  date: string;
  impressions_maps_desktop: number | null;
  impressions_maps_mobile: number | null;
  impressions_search_desktop: number | null;
  impressions_search_mobile: number | null;
  website_clicks: number | null;
  call_clicks: number | null;
  direction_requests: number | null;
  conversations: number | null;
  bookings: number | null;
}

export interface PerformanceResponse {
  points: PerformancePoint[];
  /** Keyed by metric name. A metric Google did not report is absent, not zero. */
  totals: Record<string, number>;
  source: DataSource;
}

export interface SearchTerm {
  location_id: string;
  location_title: string | null;
  /** `YYYY-MM`. Google reports search terms by month, never by day. */
  year_month: string;
  search_term: string;
  /**
   * The impression count, or the threshold Google reported instead of one when
   * `is_threshold` is true — in that case the real figure is below this number.
   */
  impressions: number | null;
  /** True when Google withheld the exact count because the term is low volume. */
  is_threshold: boolean;
  source: DataSource;
}

export interface SearchTermList {
  items: SearchTerm[];
  total: number;
  limit: number;
  offset: number;
}

export interface MediaSummary {
  location_id: string;
  location_title: string;
  photo_count: number;
  interior_photo_count: number;
  exterior_photo_count: number;
  team_photo_count: number;
  video_count: number;
  has_profile_photo: boolean;
  has_cover_photo: boolean;
  last_photo_uploaded_on: string | null;
  source: DataSource;
}

export interface MediaSummaryList {
  items: MediaSummary[];
}

/** The four impression fields, kept split because surface and device are the point. */
export const IMPRESSION_METRIC_KEYS = [
  "impressions_maps_desktop",
  "impressions_maps_mobile",
  "impressions_search_desktop",
  "impressions_search_mobile",
] as const;

export type ImpressionMetricKey = (typeof IMPRESSION_METRIC_KEYS)[number];

/** What a customer did after finding the profile. */
export const ACTION_METRIC_KEYS = [
  "website_clicks",
  "call_clicks",
  "direction_requests",
  "conversations",
  "bookings",
] as const;

export type ActionMetricKey = (typeof ACTION_METRIC_KEYS)[number];

export type PerformanceMetricKey = ImpressionMetricKey | ActionMetricKey;

/** Search terms are read rather than scanned, so a page stays small enough to render. */
export const SEARCH_TERMS_PAGE_SIZE = 25;

export interface PerformanceParams {
  locationId?: string;
  projectId?: string;
  /** `YYYY-MM-DD`, inclusive. */
  from?: string;
  /** `YYYY-MM-DD`, inclusive. */
  to?: string;
}

export interface SearchTermParams {
  locationId?: string;
  /** `YYYY-MM`. Omitted, the API returns every month it holds. */
  yearMonth?: string;
  limit?: number;
  offset?: number;
}

export interface MediaParams {
  locationId?: string;
}

function searchSuffix(query: URLSearchParams) {
  const search = query.toString();
  return search ? `?${search}` : "";
}

export const insightsApi = {
  performance: ({
    locationId,
    projectId,
    from,
    to,
  }: PerformanceParams = {}) => {
    const query = new URLSearchParams();
    if (locationId) query.set("location_id", locationId);
    if (projectId) query.set("project_id", projectId);
    if (from) query.set("from", from);
    if (to) query.set("to", to);
    return apiRequest<PerformanceResponse>(
      `/insights/performance${searchSuffix(query)}`,
    );
  },
  searchTerms: ({
    locationId,
    yearMonth,
    limit,
    offset,
  }: SearchTermParams = {}) => {
    const query = new URLSearchParams();
    if (locationId) query.set("location_id", locationId);
    if (yearMonth) query.set("year_month", yearMonth);
    if (limit !== undefined) query.set("limit", String(limit));
    if (offset !== undefined) query.set("offset", String(offset));
    return apiRequest<SearchTermList>(
      `/insights/search-terms${searchSuffix(query)}`,
    );
  },
  media: ({ locationId }: MediaParams = {}) => {
    const query = new URLSearchParams();
    if (locationId) query.set("location_id", locationId);
    return apiRequest<MediaSummaryList>(
      `/insights/media${searchSuffix(query)}`,
    );
  },
};
