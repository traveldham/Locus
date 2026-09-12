import type { ReactNode } from "react";

export default function InsightsLayout({ children }: { children: ReactNode }) {
  return <div className="px-5 py-8 lg:px-8 lg:py-10">{children}</div>;
}
