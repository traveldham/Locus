import { LocationsView } from "@/components/locations/locations-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Profiles",
  description: "Every business profile imported into this organization.",
};

export default function LocationsPage() {
  return <LocationsView />;
}
