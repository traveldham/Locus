import { PerformanceView } from "@/components/insights/performance-view";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Performance",
  description:
    "How people found your Google profiles and what they did next, exactly as Google reported it.",
};

export default function PerformancePage() {
  return <PerformanceView />;
}
