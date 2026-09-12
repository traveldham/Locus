import { LocationDetailView } from "@/components/locations/location-detail-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Location",
};

export default async function LocationDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <LocationDetailView locationId={id} />;
}
