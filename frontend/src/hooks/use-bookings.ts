"use client";

import { useActiveProjectId } from "@/contexts/active-project";

import { bookingsApi, type BookingListParams } from "@/services/api/bookings";
import { useQuery } from "@tanstack/react-query";

export const bookingKeys = {
  all: ["bookings"] as const,
  list: (params: BookingListParams) =>
    [...bookingKeys.all, "list", params] as const,
  count: (params: BookingListParams) =>
    [...bookingKeys.all, "count", params] as const,
};

export function useBookingsQuery(params: BookingListParams) {
  const projectId = useActiveProjectId();
  // An explicit project on the caller wins; otherwise the dashboard's active one.
  // A caller naming one location has already chosen its scope; narrowing that by the
  // active project as well would return nothing whenever the location sits outside it.
  const scoped = {
    projectId: params.locationId ? undefined : (projectId ?? undefined),
    ...params,
  };
  return useQuery({
    queryKey: bookingKeys.list(scoped),
    queryFn: () => bookingsApi.list(scoped),
    retry: 1,
    staleTime: 30_000,
    placeholderData: (previous) => previous,
  });
}

/**
 * Reads only `total` for a narrower slice of the same scope — the API returns the
 * count for the whole filter, so a single row is enough to read it.
 */
export function useBookingCountQuery(
  scoped: BookingListParams,
  enabled = true,
) {
  const resolved: BookingListParams = { ...scoped, limit: 1, offset: 0 };

  return useQuery({
    queryKey: bookingKeys.count(resolved),
    queryFn: () => bookingsApi.list(resolved),
    enabled,
    retry: 1,
    staleTime: 30_000,
    select: (data) => data.total,
  });
}
