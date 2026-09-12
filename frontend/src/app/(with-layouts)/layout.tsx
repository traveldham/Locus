"use client";

import Header from "@/components/common/header";
import Sidebar from "@/components/common/sidebar";
import { SheetContent, SheetOverlay, SheetTitle } from "@/components/tailgrids/core/sheet";
import { cn } from "@/utils/cn";
import { ReactNode, useState } from "react";
import { AuthGuard } from "@/components/auth/auth-guard";

export default function WithLayout({ children }: { children: ReactNode }) {
  // XL+ sidebar expand/collapse state (pinned open/closed via the toggle button)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  // Temporary hover expand, only relevant while the pinned state is collapsed
  const [isSidebarHovered, setIsSidebarHovered] = useState(false);
  // Mobile sheet open state (< xl breakpoint)
  const [isMobileSheetOpen, setIsMobileSheetOpen] = useState(false);

  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev);
  const isSidebarExpanded = isSidebarOpen || isSidebarHovered;

  return (
    <AuthGuard>
    <div className="flex h-full">
      {/*  Desktop sidebar (xl+) — always in DOM, toggles width  */}
      <aside
        onMouseEnter={() => setIsSidebarHovered(true)}
        onMouseLeave={() => setIsSidebarHovered(false)}
        style={{
          width: isSidebarExpanded ? "270px" : "72px",
          minWidth: isSidebarExpanded ? "270px" : "72px",
          transition:
            "width 300ms cubic-bezier(0.4,0,0.2,1), min-width 300ms cubic-bezier(0.4,0,0.2,1)",
        }}
        className="hidden shrink-0 overflow-hidden xl:block"
      >
        <Sidebar isSidebarOpen={isSidebarExpanded} toggleSidebar={toggleSidebar} />
      </aside>

      {/*  Mobile sidebar (< xl) — Sheet sliding from the left  */}

      <SheetOverlay isOpen={isMobileSheetOpen} onOpenChange={setIsMobileSheetOpen}>
        <SheetContent
          side="left"
          showCloseButton={false}
          className="w-67.5! max-w-67.5! border-r border-white/10 bg-background-gray-secondary_alt_2 p-0"
        >
          <SheetTitle className="sr-only">Sidebar</SheetTitle>
          <Sidebar
            isSidebarOpen={true}
            toggleSidebar={() => {
              setIsMobileSheetOpen(false);
            }}
            onItemClick={() => {
              setIsMobileSheetOpen(false);
            }}
            isMobileSheet
          />
        </SheetContent>
      </SheetOverlay>

      {/*  Main content column  */}
      <div className={cn("min-w-0 flex-1", isSidebarExpanded ? "lg:p-4 xl:pr-4" : "lg:py-4 xl:px-4")}>
        <div className="flex h-full flex-col overflow-hidden border-[0.5px] border-card-surface-border bg-card-surface-area lg:rounded-2xl lg:shadow-[0_3px_6px_-2px_rgba(0,0,0,0.02),0_1px_1px_0_rgba(0,0,0,0.04)]">
          <Header onMenuClick={() => setIsMobileSheetOpen(true)} />

          <main className="scrollbar-thin flex-1 min-h-0 overflow-y-auto">
            <div className="mx-auto w-full max-w-384 pb-5">{children}</div>
          </main>
        </div>
      </div>
    </div>
    </AuthGuard>
  );
}
