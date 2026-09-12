"use client";

import {
  LOCATIONS_MAX_PAGE_SIZE,
  locationsApi,
  type LocationEditRequest,
  type LocationListParams,
  type ProfileAction,
} from "@/services/api/locations";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const locationKeys = {
  all: ["locations"] as const,
  list: (params: LocationListParams) => [...locationKeys.all, "list", params] as const,
  detail: (id: string) => [...locationKeys.all, "detail", id] as const,
  actions: (id: string) => [...locationKeys.all, "actions", id] as const,
  attributeCatalog: () => [...locationKeys.all, "attribute-catalog"] as const,
};

/** Statuses that are still moving, so the audit trail is worth re-reading. */
const IN_FLIGHT_STATUSES: ProfileAction["status"][] = ["pending", "approved", "executing"];

/**
 * The API pages at 50 by default and caps at 200. The list surfaces ask for the
 * full page so their in-page search and sort act on everything that was loaded.
 */
export function useLocationsQuery(params: LocationListParams = {}) {
  const resolved: LocationListParams = { limit: LOCATIONS_MAX_PAGE_SIZE, ...params };

  return useQuery({
    queryKey: locationKeys.list(resolved),
    queryFn: () => locationsApi.list(resolved),
    retry: 1,
    staleTime: 30_000,
  });
}

export function useLocationQuery(id: string) {
  return useQuery({
    queryKey: locationKeys.detail(id),
    queryFn: () => locationsApi.get(id),
    enabled: Boolean(id),
    retry: 1,
    staleTime: 30_000,
  });
}

export function useAttributeCatalogQuery() {
  return useQuery({
    queryKey: locationKeys.attributeCatalog(),
    queryFn: locationsApi.attributeCatalog,
    retry: 1,
    staleTime: 5 * 60_000,
  });
}

/**
 * The audit trail for one location. Google applies an edit asynchronously, so the
 * list keeps refreshing while any action has not reached a final status.
 */
export function useLocationActionsQuery(id: string) {
  return useQuery({
    queryKey: locationKeys.actions(id),
    queryFn: () => locationsApi.listActions(id),
    enabled: Boolean(id),
    retry: 1,
    staleTime: 15_000,
    refetchInterval: (query) =>
      query.state.data?.some((action) => IN_FLIGHT_STATUSES.includes(action.status))
        ? 8_000
        : false,
  });
}

/**
 * Dry-runs an edit. It is deliberately not cached: the person editing must always
 * confirm against a diff the API produced for the exact payload being sent.
 */
export function useLocationEditPreviewMutation(id: string) {
  return useMutation({
    mutationFn: (input: LocationEditRequest) => locationsApi.previewEdit(id, input),
  });
}

/** Applies an edit to the live Google listing. */
export function useApplyLocationEditMutation(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: LocationEditRequest) => locationsApi.applyEdit(id, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: locationKeys.all }),
  });
}
