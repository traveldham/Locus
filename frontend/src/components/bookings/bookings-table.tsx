"use client";

import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRoot,
  TableRow,
} from "@/components/tailgrids/core/table";
import type { Booking } from "@/services/api/bookings";
import { formatDate, formatDateTime } from "@/utils/format-date";
import { BookingSourceChip, BookingStatusChip } from "./booking-chips";

export function BookingsTable({
  bookings,
  /** Hidden when the list is already scoped to one location. */
  showLocation = true,
}: {
  bookings: Booking[];
  showLocation?: boolean;
}) {
  return (
    <TableRoot className="min-w-[58rem]">
      <caption className="sr-only">
        Bookings, with the customer, service, requested date, status and where the booking
        came from.
      </caption>
      <TableHeader className="bg-background-gray-secondary">
        <TableRow>
          <TableHead scope="col" className="w-[18%]">
            Customer
          </TableHead>
          <TableHead scope="col" className="w-[20%]">
            Service
          </TableHead>
          {showLocation ? (
            <TableHead scope="col" className="w-[18%]">
              Location
            </TableHead>
          ) : null}
          <TableHead scope="col" className="w-[14%]">
            Requested for
          </TableHead>
          <TableHead scope="col" className="w-[12%]">
            Status
          </TableHead>
          <TableHead scope="col" className="w-[12%]">
            Source
          </TableHead>
          <TableHead scope="col" className="w-[16%]">
            Created
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {bookings.map((booking) => (
          <TableRow key={booking.id} className="transition hover:bg-background-gray-secondary">
            <TableCell className="text-text-primary">
              <span className="block max-w-48 truncate" title={booking.customer_name}>
                {booking.customer_name}
              </span>
              <span className="mt-0.5 block text-xs text-text-tertiary tabular-nums" title={booking.external_booking_id}>
                {booking.external_booking_id}
              </span>
            </TableCell>
            <TableCell className="text-text-secondary">
              <span className="block max-w-56 truncate" title={booking.service}>
                {booking.service}
              </span>
            </TableCell>
            {showLocation ? (
              <TableCell className="text-text-secondary">
                <span className="block max-w-48 truncate" title={booking.location_title}>
                  {booking.location_title}
                </span>
              </TableCell>
            ) : null}
            <TableCell className="whitespace-nowrap text-text-secondary tabular-nums">
              {formatDate(booking.requested_for_date) ?? booking.requested_for_date}
            </TableCell>
            <TableCell className="py-2">
              <BookingStatusChip status={booking.status} />
            </TableCell>
            <TableCell className="py-2">
              <BookingSourceChip source={booking.booking_source} />
            </TableCell>
            <TableCell className="whitespace-nowrap text-text-secondary tabular-nums">
              {formatDateTime(booking.created_at) ?? booking.created_at}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </TableRoot>
  );
}
