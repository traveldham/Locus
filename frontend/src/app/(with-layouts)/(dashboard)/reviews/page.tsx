import { ReviewsView } from "@/components/reviews/reviews-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Reviews",
  description: "Every Google review across your locations, with the replies you have published.",
};

export default function ReviewsPage() {
  return <ReviewsView />;
}
