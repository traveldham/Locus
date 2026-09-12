"use client";

import { postsApi, type PostListParams } from "@/services/api/posts";
import { useQuery } from "@tanstack/react-query";

export function usePostsQuery(params: PostListParams) {
  return useQuery({
    queryKey: ["posts", params],
    queryFn: () => postsApi.list(params),
    retry: 1,
    staleTime: 30_000,
    placeholderData: (previous) => previous,
  });
}
