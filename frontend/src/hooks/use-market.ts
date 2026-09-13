"use client";

import {
  marketApi,
  type CompetitorParams,
  type RankHistoryParams,
} from "@/services/api/market";
import { useQuery } from "@tanstack/react-query";

export const marketKeys = {
  all: ["market"] as const,
  keywords: (locationId: string) =>
    [...marketKeys.all, "keywords", locationId] as const,
  rankings: (params: RankHistoryParams) =>
    [...marketKeys.all, "rankings", params] as const,
  competitors: (params: CompetitorParams) =>
    [...marketKeys.all, "competitors", params] as const,
};

/** Rankings move once a week, so the cached copy stays fresh for a good while. */
const RANK_STALE_TIME = 5 * 60_000;

export function useTrackedKeywordsQuery(locationId: string | null) {
  return useQuery({
    queryKey: marketKeys.keywords(locationId ?? ""),
    queryFn: () => marketApi.listKeywords(locationId as string),
    enabled: Boolean(locationId),
    retry: 1,
    staleTime: RANK_STALE_TIME,
  });
}

export function useRankHistoryQuery(
  trackedKeywordId: string | null,
  range: { from?: string; to?: string } = {},
) {
  const params: RankHistoryParams = {
    trackedKeywordId: trackedKeywordId ?? "",
    ...range,
  };

  return useQuery({
    queryKey: marketKeys.rankings(params),
    queryFn: () => marketApi.getRankings(params),
    enabled: Boolean(trackedKeywordId),
    retry: 1,
    staleTime: RANK_STALE_TIME,
  });
}

export function useCompetitorsQuery(
  trackedKeywordId: string | null,
  weekStart: string | null,
) {
  const params: CompetitorParams = {
    trackedKeywordId: trackedKeywordId ?? "",
    weekStart: weekStart ?? undefined,
  };

  return useQuery({
    queryKey: marketKeys.competitors(params),
    queryFn: () => marketApi.listCompetitors(params),
    enabled: Boolean(trackedKeywordId),
    retry: 1,
    staleTime: RANK_STALE_TIME,
  });
}
