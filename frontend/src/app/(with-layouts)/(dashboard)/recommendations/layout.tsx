import type { Metadata } from "next";
import { Suspense, type ReactNode } from "react";

export const metadata: Metadata = {
  title: "Location audit",
  description: "A health score, issues and evidence for each location.",
};

export default function RecommendationsLayout({ children }: { children: ReactNode }) {
  // The audit reads `?run=` and its filters from the URL, which needs a boundary above.
  return <Suspense fallback={null}>{children}</Suspense>;
}
