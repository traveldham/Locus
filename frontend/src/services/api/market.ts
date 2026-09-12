import { apiRequest } from "./client";

/**
 * Where a row came from. Google supplies no ranking or competitor data at all, so
 * everything this module returns is `locus` — the API states it per response rather
 * than the client assuming it, so the mark on screen always follows the data.
 */
export type DataSource = "google" | "locus";

export type SearchIntent =
  | "general"
  | "emergency"
  | "cosmetic"
  | "pediatric"
  | "implants"
  | "orthodontics"
  | "insurance";

export interface TrackedKeyword {
  id: string;
  location_id: string;
  keyword: string;
  search_intent: SearchIntent;
  device: string;
  tracking_started_on: string;
  /** The most recent absolute position, or null when the business was not found. */
  latest_rank: number | null;
  source: DataSource;
}

export interface RankPoint {
  week_start: string;
  /**
   * Absolute position in the result page. `null` means the business was not found
   * at all that week — an outcome, not a missing reading.
   */
  rank_absolute: number | null;
  /** Position within the three-result local pack, 1–3, or null when outside it. */
  rank_in_local_pack: number | null;
  found: boolean;
  result_url: string | null;
}

export interface Competitor {
  competitor_name: string;
  competitor_place_id: string;
  rank_absolute: number | null;
  review_count: number | null;
  average_rating: number | null;
  photo_count: number | null;
  is_claimed: boolean;
}

export interface TrackedKeywordList {
  items: TrackedKeyword[];
}

export interface RankHistory {
  points: RankPoint[];
  source: DataSource;
}

export interface CompetitorList {
  items: Competitor[];
  total: number;
  week_start: string | null;
  source: DataSource;
}

export interface RankHistoryParams {
  trackedKeywordId: string;
  /** ISO dates; both optional, in which case the API picks its own window. */
  from?: string;
  to?: string;
}

export interface CompetitorParams {
  trackedKeywordId: string;
  weekStart?: string;
}

/** The intents the API can return, in the order the product lists them. */
export const SEARCH_INTENTS: SearchIntent[] = [
  "general",
  "emergency",
  "cosmetic",
  "pediatric",
  "implants",
  "orthodontics",
  "insurance",
];

export const SEARCH_INTENT_LABELS: Record<SearchIntent, string> = {
  general: "General",
  emergency: "Emergency",
  cosmetic: "Cosmetic",
  pediatric: "Pediatric",
  implants: "Implants",
  orthodontics: "Orthodontics",
  insurance: "Insurance",
};

export function searchIntentLabel(intent: SearchIntent | string) {
  return SEARCH_INTENT_LABELS[intent as SearchIntent] ?? intent;
}

export const marketApi = {
  listKeywords: (locationId: string) => {
    const query = new URLSearchParams({ location_id: locationId });
    return apiRequest<TrackedKeywordList>(`/market/keywords?${query.toString()}`);
  },
  getRankings: ({ trackedKeywordId, from, to }: RankHistoryParams) => {
    const query = new URLSearchParams({ tracked_keyword_id: trackedKeywordId });
    if (from) query.set("from", from);
    if (to) query.set("to", to);
    return apiRequest<RankHistory>(`/market/rankings?${query.toString()}`);
  },
  listCompetitors: ({ trackedKeywordId, weekStart }: CompetitorParams) => {
    const query = new URLSearchParams({ tracked_keyword_id: trackedKeywordId });
    if (weekStart) query.set("week_start", weekStart);
    return apiRequest<CompetitorList>(`/market/competitors?${query.toString()}`);
  },
};
