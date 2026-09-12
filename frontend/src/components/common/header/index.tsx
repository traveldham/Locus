"use client";

import { MenuIcon } from "@/components/common/header/icons";
import ThemeToggle from "@/components/common/header/theme-toggle";
import { UserProfileButton } from "@/components/common/header/user-profile";
import { ThreeDots } from "@/components/common/sidebar/icon";
import { cn } from "@/utils/cn";
import { BrandLogo } from "@/components/common/brand-logo";
import React from "react";

//  Main Header
export default function Header({ onMenuClick }: { onMenuClick?: () => void }) {
  const [isDrawerOpen, setIsDrawerOpen] = React.useState(false);

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b-[0.5px] border-card-border bg-card-surface-area px-2 py-4 lg:px-5">
        {/*  Mobile layout (< xl)  3-column grid: menu | logo | dots */}
        <div className="flex items-center xl:hidden">
          {/* Left: Menu / Hamburger */}
          <div className="flex flex-1 justify-start">
            <button
              id="mobile-menu-toggle"
              onClick={onMenuClick}
              aria-label="Open sidebar menu"
              className="flex size-11 items-center justify-center rounded-lg text-icon-tertiary transition-colors hover:bg-background-gray-secondary hover:text-text-primary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
            >
              <MenuIcon />
            </button>
          </div>

          {/* Center: Logo */}
          <div className="flex items-center justify-center">
            <BrandLogo />
          </div>

          {/* Right: Three-dot */}
          <div className="flex flex-1 justify-end">
            <button
              id="mobile-info-toggle"
              onClick={() => setIsDrawerOpen(!isDrawerOpen)}
              aria-label="Open quick access"
              className={cn(
                "flex size-11 items-center justify-center rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600",
                isDrawerOpen
                  ? "bg-background-gray-secondary text-text-primary"
                  : "text-icon-tertiary hover:text-text-primary",
              )}
            >
              <ThreeDots />
            </button>
          </div>
        </div>

        {/* Desktop layout (xl+) - original layout */}
        <div className="hidden items-center justify-between xl:flex">
          {/* Left Side - Search */}
          <p className="text-sm font-medium text-text-secondary">Organization workspace</p>

          {/* Right Side - Actions */}
          <div className="flex items-center gap-2.5">
            <ThemeToggle />
            <UserProfileButton />
          </div>
        </div>
      </header>

      {/* Mobile Info */}
      <MobileInfoDrawer isOpen={isDrawerOpen} />
    </>
  );
}

// Mobile Info
function MobileInfoDrawer({ isOpen }: { isOpen: boolean }) {
  return (
    <div className={cn("xl:hidden", isOpen ? "block" : "hidden")}>
      <div className="px-5 py-4 shadow-xs">
        <div className="flex items-center justify-between gap-2.5">
          <div className="flex items-center gap-2.5">
            <ThemeToggle />
          </div>

          {/* Right Side - Actions */}
          <UserProfileButton />
        </div>
      </div>
    </div>
  );
}
