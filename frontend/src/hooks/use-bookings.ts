"use client";

import { bookingsApi, type BookingListParams } from "@/services/api/bookings";
import { useQuery } from "@tanstack/react-query";

export const bookingKeys = {
  all: ["bookings"] as const,
  list: (params: BookingListParams) => [...bookingKeys.all, "list", params] as const,
  count: (params: BookingListParams) => [...bookingKeys.all, "count", params] as const,
};

export function useBookingsQuery(params: BookingListParams) {
  return useQuery({
    queryKey: bookingKeys.list(params),
    queryFn: () => bookingsApi.list(params),
    retry: 1,
    staleTime: 30_000,
    placeholderData: (previous) => previous,
  });
}

/**
 * Reads only `total` for a narrower slice of the same scope — the API returns the
 * count for the whole filter, so a single row is enough to read it.
 */
export function useBookingCountQuery(params: BookingListParams, enabled = true) {
  const resolved: BookingListParams = { ...params, limit: 1, offset: 0 };

  return useQuery({
    queryKey: bookingKeys.count(resolved),
    queryFn: () => bookingsApi.list(resolved),
    enabled,
    retry: 1,
    staleTime: 30_000,
    select: (data) => data.total,
  });
}
