import { SearchTermsView } from "@/components/insights/search-terms-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Search terms",
  description:
    "The queries people typed before Google showed them your profile, with the impressions each one earned.",
};

export default function SearchTermsPage() {
  return <SearchTermsView />;
}
