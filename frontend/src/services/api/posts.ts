import { apiRequest } from "./client";
import type { DataSource } from "./insights";

export type PostType = "standard" | "event" | "offer" | "alert";
export type PostCtaType = "book" | "call" | "learn_more" | "sign_up" | "get_offer";

export interface Post {
  id: string;
  location_id: string;
  location_title: string | null;
  google_post_id: string;
  post_type: PostType;
  summary: string | null;
  cta_type: PostCtaType | null;
  published_on: string | null;
  source: DataSource;
}

export interface PostList {
  items: Post[];
  total: number;
  limit: number;
  offset: number;
  source: DataSource;
}

export interface PostListParams {
  locationId?: string;
  postType?: PostType;
  limit?: number;
  offset?: number;
}

export const POSTS_PAGE_SIZE = 25;

export const postsApi = {
  list(params: PostListParams = {}) {
    const query = new URLSearchParams();
    if (params.locationId) query.set("location_id", params.locationId);
    if (params.postType) query.set("post_type", params.postType);
    if (params.limit !== undefined) query.set("limit", String(params.limit));
    if (params.offset !== undefined) query.set("offset", String(params.offset));
    const search = query.toString();
    return apiRequest<PostList>(`/posts${search ? `?${search}` : ""}`);
  },
};
