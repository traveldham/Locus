"use client";

import {
  insightsApi,
  SEARCH_TERMS_PAGE_SIZE,
  type MediaParams,
  type PerformanceParams,
  type SearchTermParams,
} from "@/services/api/insights";
import { useQuery } from "@tanstack/react-query";

export const insightKeys = {
  all: ["insights"] as const,
  performance: (params: PerformanceParams) =>
    [...insightKeys.all, "performance", params] as const,
  searchTerms: (params: SearchTermParams) =>
    [...insightKeys.all, "search-terms", params] as const,
  media: (params: MediaParams) => [...insightKeys.all, "media", params] as const,
};

/**
 * Google finalises a day's performance reporting well after the day ends, so the
 * answer for a given range barely moves. A long stale time keeps range switching
 * instant without hiding a real update.
 */
const PERFORMANCE_STALE_TIME = 5 * 60_000;

export function usePerformanceQuery(params: PerformanceParams = {}) {
  return useQuery({
    queryKey: insightKeys.performance(params),
    queryFn: () => insightsApi.performance(params),
    retry: 1,
    staleTime: PERFORMANCE_STALE_TIME,
  });
}

/** Search terms are reported per month, so the page size is fixed by the surface. */
export function useSearchTermsQuery(params: SearchTermParams = {}) {
  const resolved: SearchTermParams = {
    limit: SEARCH_TERMS_PAGE_SIZE,
    ...params,
  };

  return useQuery({
    queryKey: insightKeys.searchTerms(resolved),
    queryFn: () => insightsApi.searchTerms(resolved),
    retry: 1,
    staleTime: PERFORMANCE_STALE_TIME,
  });
}

export function useMediaSummaryQuery(params: MediaParams = {}) {
  return useQuery({
    queryKey: insightKeys.media(params),
    queryFn: () => insightsApi.media(params),
    retry: 1,
    staleTime: PERFORMANCE_STALE_TIME,
  });
}
