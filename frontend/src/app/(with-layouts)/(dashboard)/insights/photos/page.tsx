import { PhotosView } from "@/components/insights/photos-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Photos",
  description:
    "Photo and video counts across your profiles, with the profile and cover photos Google shows first.",
};

export default function PhotosPage() {
  return <PhotosView />;
}
