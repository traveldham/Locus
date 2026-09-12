"use client";

import {
  reviewsApi,
  type ReplyToReviewInput,
  type ReviewListParams,
  type SyncReviewsInput,
} from "@/services/api/reviews";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const reviewKeys = {
  all: ["reviews"] as const,
  list: (params: ReviewListParams) => [...reviewKeys.all, "list", params] as const,
  detail: (id: string) => [...reviewKeys.all, "detail", id] as const,
};

/**
 * The list is paged on the server, so the previous page stays on screen while the
 * next one loads rather than collapsing the inbox back to a skeleton.
 */
export function useReviewsQuery(params: ReviewListParams = {}) {
  return useQuery({
    queryKey: reviewKeys.list(params),
    queryFn: () => reviewsApi.list(params),
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
 * Counts the reviews still waiting on a reply within the caller's other filters.
 * Only `total` is read, so the page size is the smallest the API accepts.
 */
export function useUnrepliedReviewCountQuery(
  params: Omit<ReviewListParams, "replied" | "limit" | "offset"> = {},
  { enabled = true }: { enabled?: boolean } = {},
) {
  const resolved: ReviewListParams = { ...params, replied: false, limit: 1, offset: 0 };

  return useQuery({
    queryKey: reviewKeys.list(resolved),
    queryFn: () => reviewsApi.list(resolved),
    enabled,
    placeholderData: keepPreviousData,
    retry: 1,
    staleTime: 30_000,
    select: (data) => data.total,
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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: reviewKeys.all }),
  });
}
