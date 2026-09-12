import { apiRequest } from "./client";

export interface Review {
  id: string;
  location_id: string;
  location_title: string;
  google_review_id: string;
  google_review_name: string | null;
  /** Null when Google withheld the name; pair with `is_anonymous` before rendering. */
  reviewer_display_name: string | null;
  is_anonymous: boolean;
  /** Whole stars, 1 through 5. */
  star_rating: number;
  comment: string | null;
  create_time: string;
  update_time: string | null;
  /** The reply the business owner published on Google, if any. */
  reply_comment: string | null;
  reply_update_time: string | null;
  has_reply: boolean;
}

export interface ReviewList {
  items: Review[];
  total: number;
  limit: number;
  offset: number;
}

/** What a finished sync did. The endpoint answers once Google has been read, not before. */
export interface ReviewSyncResult {
  sync_run_id: string;
  locations_synced: number;
  created: number;
  updated: number;
  total: number;
  /** Locations whose reviews could not be fetched, each with the reason. */
  skipped: { location_id: string; reason: string }[];
}

/** The API caps a page at 200 reviews however large a limit is requested. */
export const REVIEWS_MAX_PAGE_SIZE = 200;

/** The inbox reads rather than scans, so it asks for a page it can render in full. */
export const REVIEWS_PAGE_SIZE = 25;

/** Google refuses a longer reply, so the composer stops before the request is made. */
export const REPLY_MAX_LENGTH = 4096;

export const REVIEW_STAR_RATINGS = [5, 4, 3, 2, 1] as const;

export interface ReviewListParams {
  /** Restrict to the reviews of the locations in one project. */
  projectId?: string;
  locationId?: string;
  /** Whole stars, 1 through 5. */
  rating?: number;
  /** True for reviews that already carry an owner reply, false for those that do not. */
  replied?: boolean;
  /** Server-side search across the reviewer name and the review text. */
  q?: string;
  /** Defaults to 50 on the API; hard capped at 200. */
  limit?: number;
  offset?: number;
}

export interface ReplyToReviewInput {
  id: string;
  /** Published publicly on Google under the business name. */
  comment: string;
}

export interface SyncReviewsInput {
  /** Omit to sync every location the organization has imported. */
  location_id?: string;
}

function reviewReplyPath(id: string) {
  return `/reviews/${encodeURIComponent(id)}/reply`;
}

export const reviewsApi = {
  list: ({ projectId, locationId, rating, replied, q, limit, offset }: ReviewListParams = {}) => {
    const query = new URLSearchParams();
    if (projectId) query.set("project_id", projectId);
    if (locationId) query.set("location_id", locationId);
    if (rating !== undefined) query.set("rating", String(rating));
    if (replied !== undefined) query.set("replied", String(replied));
    if (q) query.set("q", q);
    if (limit !== undefined) query.set("limit", String(limit));
    if (offset !== undefined) query.set("offset", String(offset));
    const search = query.toString();
    return apiRequest<ReviewList>(`/reviews${search ? `?${search}` : ""}`);
  },
  get: (id: string) => apiRequest<Review>(`/reviews/${encodeURIComponent(id)}`),
  /** Creates the reply, or replaces the one already published. */
  reply: ({ id, comment }: ReplyToReviewInput) =>
    apiRequest<Review>(reviewReplyPath(id), {
      method: "PUT",
      body: JSON.stringify({ comment }),
    }),
  /** Removes the owner reply only. Google offers no way to remove the review itself. */
  removeReply: (id: string) => apiRequest<Review>(reviewReplyPath(id), { method: "DELETE" }),
  sync: (input: SyncReviewsInput = {}) =>
    apiRequest<ReviewSyncResult>("/reviews/sync", {
      method: "POST",
      body: JSON.stringify(input),
    }),
};
