"use client";

import { useActiveProjectId } from "@/contexts/active-project";

import { postsApi, type PostListParams } from "@/services/api/posts";
import { useQuery } from "@tanstack/react-query";

export function usePostsQuery(params: PostListParams) {
  const projectId = useActiveProjectId();
  // An explicit project on the caller wins; otherwise the dashboard's active one.
  // A caller naming one location has already chosen its scope; narrowing that by the
  // active project as well would return nothing whenever the location sits outside it.
  const scoped = {
    projectId: params.locationId ? undefined : (projectId ?? undefined),
    ...params,
  };
  return useQuery({
    queryKey: ["posts", scoped],
    queryFn: () => postsApi.list(scoped),
    retry: 1,
    staleTime: 30_000,
    placeholderData: (previous) => previous,
  });
}
