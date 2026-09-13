import { apiRequest } from "./client";
import type { DataSource } from "./market";

export type BookingStatus =
  | "new"
  | "confirmed"
  | "completed"
  | "cancelled"
  | "no_show";

export type BookingSource = "website" | "google_profile" | "phone" | "walk_in";

export interface Booking {
  id: string;
  location_id: string;
  location_title: string;
  external_booking_id: string;
  customer_name: string;
  service: string;
  requested_for_date: string;
  status: BookingStatus;
  booking_source: BookingSource;
  created_at: string;
  /** Google reports only an aggregate count, so individual bookings are always Locus data. */
  source: DataSource;
}

export interface BookingList {
  items: Booking[];
  total: number;
  limit: number;
  offset: number;
}

export interface BookingListParams {
  /** Narrows the request to one project's locations. */
  projectId?: string;
  locationId?: string;
  status?: BookingStatus;
  bookingSource?: BookingSource;
  limit?: number;
  offset?: number;
}

export const BOOKINGS_PAGE_SIZE = 25;

export const BOOKING_STATUSES: BookingStatus[] = [
  "new",
  "confirmed",
  "completed",
  "cancelled",
  "no_show",
];

export const BOOKING_SOURCES: BookingSource[] = [
  "website",
  "google_profile",
  "phone",
  "walk_in",
];

export const BOOKING_STATUS_LABELS: Record<BookingStatus, string> = {
  new: "New",
  confirmed: "Confirmed",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No show",
};

export const BOOKING_SOURCE_LABELS: Record<BookingSource, string> = {
  website: "Website",
  google_profile: "Google listing",
  phone: "Phone",
  walk_in: "Walk-in",
};

export function bookingStatusLabel(status: BookingStatus | string) {
  return BOOKING_STATUS_LABELS[status as BookingStatus] ?? status;
}

export function bookingSourceLabel(source: BookingSource | string) {
  return BOOKING_SOURCE_LABELS[source as BookingSource] ?? source;
}

function bookingsQuery({
  locationId,
  projectId,
  status,
  bookingSource,
  limit,
  offset,
}: BookingListParams) {
  const query = new URLSearchParams();
  if (locationId) query.set("location_id", locationId);
  if (projectId) query.set("project_id", projectId);
  if (status) query.set("status", status);
  if (bookingSource) query.set("booking_source", bookingSource);
  if (limit !== undefined) query.set("limit", String(limit));
  if (offset !== undefined) query.set("offset", String(offset));
  return query.toString();
}

export const bookingsApi = {
  list: (params: BookingListParams = {}) => {
    const search = bookingsQuery(params);
    return apiRequest<BookingList>(`/bookings${search ? `?${search}` : ""}`);
  },
};
