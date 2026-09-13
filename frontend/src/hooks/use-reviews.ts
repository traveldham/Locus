"use client";

import { useActiveProjectId } from "@/contexts/active-project";

import {
  reviewsApi,
  type ReplyToReviewInput,
  type ReviewListParams,
  type SyncReviewsInput,
} from "@/services/api/reviews";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

export const reviewKeys = {
  all: ["reviews"] as const,
  list: (params: ReviewListParams) =>
    [...reviewKeys.all, "list", params] as const,
  detail: (id: string) => [...reviewKeys.all, "detail", id] as const,
};

/**
 * The list is paged on the server, so the previous page stays on screen while the
 * next one loads rather than collapsing the inbox back to a skeleton.
 */
export function useReviewsQuery(params: ReviewListParams = {}) {
  const projectId = useActiveProjectId();
  // An explicit project on the caller wins; otherwise the dashboard's active one.
  // A caller naming one location has already chosen its scope; narrowing that by the
  // active project as well would return nothing whenever the location sits outside it.
  const scoped = {
    projectId: params.locationId ? undefined : (projectId ?? undefined),
    ...params,
  };
  return useQuery({
    queryKey: reviewKeys.list(scoped),
    queryFn: () => reviewsApi.list(scoped),
    placeholderData: keepPreviousData,
    retry: 1,
    staleTime: 30_000,
  });
}

export function useReviewQuery(id: string) {
  return useQuery({
    queryKey: reviewKeys.detail(id),
    queryFn: () => reviewsApi.get(id),
    enabled: Boolean(id),
    retry: 1,
    staleTime: 30_000,
  });
}

/**
 * Counts all reply states within the same scope as the review list.
 * Only `total` is read, so the page size is the smallest the API accepts.
 */
export function useReviewStatusCountsQuery(
  params: Omit<ReviewListParams, "replied" | "limit" | "offset"> = {},
) {
  const projectId = useActiveProjectId();
  const resolved: ReviewListParams = {
    projectId: params.locationId ? undefined : (projectId ?? undefined),
    ...params,
    limit: 1,
    offset: 0,
  };

  return useQuery({
    queryKey: [...reviewKeys.all, "status-counts", resolved],
    queryFn: async () => {
      const [all, unreplied, replied] = await Promise.all([
        reviewsApi.list(resolved),
        reviewsApi.list({ ...resolved, replied: false }),
        reviewsApi.list({ ...resolved, replied: true }),
      ]);
      return {
        all: all.total,
        unreplied: unreplied.total,
        replied: replied.total,
      };
    },
    retry: 1,
    staleTime: 30_000,
  });
}

export function useReplyToReviewMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ReplyToReviewInput) => reviewsApi.reply(input),
    onSuccess: (review) => {
      queryClient.setQueryData(reviewKeys.detail(review.id), review);
      return queryClient.invalidateQueries({ queryKey: reviewKeys.all });
    },
  });
}

export function useRemoveReviewReplyMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => reviewsApi.removeReply(id),
    onSuccess: (review) => {
      queryClient.setQueryData(reviewKeys.detail(review.id), review);
      return queryClient.invalidateQueries({ queryKey: reviewKeys.all });
    },
  });
}

/**
 * The sync runs while the request is open and answers with what it imported, so the
 * inbox is invalidated once it returns and the new reviews are already there.
 */
export function useSyncReviewsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: SyncReviewsInput = {}) => reviewsApi.sync(input),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: reviewKeys.all }),
  });
}
