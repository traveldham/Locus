"use client";

import { locationKeys } from "@/hooks/use-locations";
import {
  projectsApi,
  type CreateProjectInput,
  type ProjectDetail,
  type ProjectListParams,
  type UpdateProjectInput,
} from "@/services/api/projects";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const projectKeys = {
  all: ["projects"] as const,
  lists: () => [...projectKeys.all, "list"] as const,
  list: (params: ProjectListParams) => [...projectKeys.lists(), params] as const,
  detail: (id: string) => [...projectKeys.all, "detail", id] as const,
};

export function useProjectsQuery(params: ProjectListParams = {}) {
  return useQuery({
    queryKey: projectKeys.list(params),
    queryFn: () => projectsApi.list(params),
    retry: 1,
    staleTime: 30_000,
  });
}

export function useProjectQuery(id: string) {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => projectsApi.get(id),
    enabled: Boolean(id),
    retry: 1,
    staleTime: 30_000,
  });
}

export function useCreateProjectMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateProjectInput) => projectsApi.create(input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: projectKeys.all }),
  });
}

/**
 * Renames or archives a project. The API answers with the project without its
 * locations, so the cached detail keeps its own `locations` and takes the rest.
 */
export function useUpdateProjectMutation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UpdateProjectInput) => projectsApi.update(id, input),
    onSuccess: (project) => {
      queryClient.setQueryData<ProjectDetail>(projectKeys.detail(id), (current) =>
        current ? { ...current, ...project } : current,
      );
      return queryClient.invalidateQueries({ queryKey: projectKeys.all });
    },
  });
}

/**
 * Links locations to the project. Adding one that is already linked is a no-op on the
 * API, so re-adding never fails. The response is the whole project with its locations.
 */
export function useAddProjectLocationsMutation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (locationIds: string[]) => projectsApi.addLocations(id, locationIds),
    onSuccess: async (detail) => {
      queryClient.setQueryData(projectKeys.detail(id), detail);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: projectKeys.all }),
        // Location lists can be scoped to a project, so their membership changed too.
        queryClient.invalidateQueries({ queryKey: locationKeys.all }),
      ]);
    },
  });
}

/** Unlinks one location from the project. The location itself is untouched. */
export function useRemoveProjectLocationMutation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (locationId: string) => projectsApi.removeLocation(id, locationId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: projectKeys.all }),
        queryClient.invalidateQueries({ queryKey: locationKeys.all }),
      ]);
    },
  });
}

/** Deletes the project and its links. The locations stay in the organization. */
export function useDeleteProjectMutation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => projectsApi.remove(id),
    // Only the lists are refreshed: refetching the detail of a project that has just
    // been deleted would flash a "not found" state on the page being navigated away from.
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: projectKeys.lists() }),
        queryClient.invalidateQueries({ queryKey: locationKeys.all }),
      ]);
    },
  });
}
