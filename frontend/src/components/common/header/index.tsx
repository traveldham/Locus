"use client";

import { MenuIcon } from "@/components/common/header/icons";
import { ProjectSwitcher } from "@/components/common/header/project-switcher";
import ThemeToggle from "@/components/common/header/theme-toggle";
import { UserProfileButton } from "@/components/common/header/user-profile";
import { ThreeDots } from "@/components/common/sidebar/icon";
import { LinkButton } from "@/components/common/link-button";
import { cn } from "@/utils/cn";
import { BrandLogo } from "@/components/common/brand-logo";
import React from "react";
import { ConnectionStatus } from "./connection-status";

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

        <div className="mt-2 flex justify-center xl:hidden">
          <ConnectionStatus />
        </div>

        {/* Desktop layout (xl+) - original layout */}
        <div className="hidden items-center justify-between xl:flex">
          {/* Left Side - project switcher, replacing the sidebar's Projects entry */}
          <div className="flex items-center gap-2.5">
            <ProjectSwitcher />
            {/* The switcher only ever opens one project, so without this the list of
                them has no way in from anywhere in the application. */}
            <AllProjectsLink />
          </div>

          {/* Right Side - Actions */}
          <div className="flex items-center gap-2.5">
            <ConnectionStatus />
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

/** The way to every project, rather than the one the switcher has open. */
function AllProjectsLink() {
  return (
    <LinkButton href="/projects" appearance="ghost" size="xl">
      All projects
    </LinkButton>
  );
}

// Mobile Info
function MobileInfoDrawer({ isOpen }: { isOpen: boolean }) {
  return (
    <div className={cn("xl:hidden", isOpen ? "block" : "hidden")}>
      <div className="px-5 py-4 shadow-xs">
        <div className="flex items-center justify-between gap-2.5">
          <div className="flex items-center gap-2.5">
            <AllProjectsLink />
            <ThemeToggle />
          </div>

          {/* Right Side - Actions */}
          <UserProfileButton />
        </div>
      </div>
    </div>
  );
}
