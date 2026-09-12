"use client";

import { cn } from "@/utils/cn";
import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/insights/performance", label: "Performance" },
  { href: "/insights/search-terms", label: "Search terms" },
  { href: "/insights/photos", label: "Photos" },
];

export function InsightsTabs() {
  const pathname = usePathname();

  return (
    <nav aria-label="Insights sections" className="border-b border-card-border">
      <ul className="-mb-px flex flex-wrap gap-x-1">
        {TABS.map((tab) => {
          const isActive = pathname === tab.href || pathname.startsWith(`${tab.href}/`);
          return (
            <li key={tab.href}>
              <Link
                href={tab.href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "flex h-11 items-center rounded-t-lg border-b-2 px-3 text-sm font-medium transition outline-none focus-visible:ring-2 focus-visible:ring-primary-500",
                  isActive
                    ? "border-primary-500 text-text-primary"
                    : "border-transparent text-text-tertiary hover:text-text-primary",
                )}
              >
                {tab.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
