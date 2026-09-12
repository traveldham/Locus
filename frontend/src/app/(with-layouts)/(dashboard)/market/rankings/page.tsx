import { RankingsView } from "@/components/market/rankings-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Keyword rankings",
  description:
    "Weekly local search position for every tracked keyword, measured by Locus rather than supplied by Google.",
};

export default function RankingsPage() {
  return <RankingsView />;
}
