import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/tailgrids/core/collapsible";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/tailgrids/core/tooltip";
import { cn } from "@/utils/cn";
import { AltArrowUpIcon } from "@/utils/icon";
import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";
import { isPathActive } from "./utils";

export interface NavItemProps {
  id?: string;
  icon?: React.ReactNode;
  label: string;
  href?: string;
  items?: Array<{ title: string; url?: string }>;
  collapsed?: boolean;
  onItemClick?: () => void;
}

export default function NavItem({
  id,
  icon,
  label,
  href,
  items,
  collapsed,
  onItemClick,
}: NavItemProps) {
  const pathname = usePathname();

  const isActive = href ? isPathActive(href, pathname) : false;

  const hasActiveChild = items?.some((item) => item.url && isPathActive(item.url, pathname));

  // Collapsed: icon-only button centered, no dropdown
  if (collapsed) {
    return (
      <div className="flex justify-center">
        <Tooltip placement="right">
          <TooltipTrigger asChild>
            <Link
              href={href ?? items?.[0]?.url ?? "#"}
              onClick={onItemClick}
              className={cn(
                "flex min-h-11 min-w-11 items-center justify-center rounded-lg px-3 py-2.5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600",
                isActive || hasActiveChild
                  ? "bg-white/10 text-white"
                  : "text-white/65 transition-colors duration-200 hover:bg-white/10 hover:text-white",
              )}
            >
              {icon}
            </Link>
          </TooltipTrigger>
          <TooltipContent>
            <p>{label}</p>
          </TooltipContent>
        </Tooltip>
      </div>
    );
  }

  // Expanded: with sub-items → collapsible
  if (items && items.length > 0) {
    return (
      <Collapsible
        id={id}
        className="border-none bg-transparent data-expanded:pb-0!"
      >
        <CollapsibleTrigger
          className={cn(
            "group/collapsible flex min-h-11 w-full items-center justify-between gap-3 rounded-lg border-none bg-transparent px-3 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 sm:px-3",
            hasActiveChild
              ? "bg-white/10 text-white"
              : "text-white/65 transition-colors duration-200 hover:bg-white/10 hover:text-white",
          )}
        >
          <div className="flex flex-1 items-center gap-3">
            <span
              className={cn(
                hasActiveChild
                  ? "text-white"
                  : "text-white/60 transition-colors duration-200 group-hover/collapsible:text-white",
              )}
            >
              {icon}
            </span>
            <span>{label}</span>
          </div>

          <AltArrowUpIcon className="rotate-180 text-white/60 duration-200 group-data-expanded:rotate-0" />
        </CollapsibleTrigger>

        <CollapsibleContent className="space-y-1 pr-0 group-data-expanded:mt-2">
          {items.map((item) => {
            const isChildActive = item.url ? isPathActive(item.url, pathname) : false;

            return (
              <div key={item.title} className="px-0">
                <Link
                  href={item.url ?? "#"}
                  onClick={onItemClick}
                  className={cn(
                    "flex min-h-11 items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600",
                    isChildActive
                      ? "bg-white/10 text-white"
                      : "text-white/65 hover:bg-white/10 hover:text-white",
                  )}
                >
                  {item.title}
                </Link>
              </div>
            );
          })}
        </CollapsibleContent>
      </Collapsible>
    );
  }

  // Expanded: simple link
  return (
    href && (
      <Link
        href={href}
        onClick={onItemClick}
        className={cn(
          "flex min-h-11 w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600",
          isActive
            ? "bg-white/10 text-white"
            : "text-white/65 hover:bg-white/10 hover:text-white",
        )}
      >
        <span className="text-white/60">{icon}</span>
        <span>{label}</span>
      </Link>
    )
  );
}
