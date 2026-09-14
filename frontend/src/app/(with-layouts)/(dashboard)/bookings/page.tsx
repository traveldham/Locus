import { BookingsView } from "@/components/bookings/bookings-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Bookings",
  description:
    "Every appointment request across your profiles, and which channel it arrived through.",
};

export default function BookingsPage() {
  return <BookingsView />;
}
