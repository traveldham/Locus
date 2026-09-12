import { LocationsView } from "@/components/locations/locations-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Locations",
  description: "Every business location imported into this organization.",
};

export default function LocationsPage() {
  return <LocationsView />;
}
