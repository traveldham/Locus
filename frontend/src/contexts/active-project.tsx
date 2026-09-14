"use client";

import { useProjectsQuery } from "@/hooks/use-projects";
import type { Project } from "@/services/api/projects";
import { useRouter, useSearchParams } from "next/navigation";
import { createContext, useContext, useEffect, type ReactNode } from "react";

const STORAGE_KEY = "locus.active-project";

function remembered(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    // Private windows and blocked site data are fine; the URL still decides.
    return null;
  }
}

function remember(id: string) {
  try {
    window.localStorage.setItem(STORAGE_KEY, id);
  } catch {
    // Non-fatal: the URL carries the choice either way.
  }
}

interface ActiveProjectValue {
  projects: Project[];
  project: Project | undefined;
  projectId: string | null;
  setProjectId: (id: string) => void;
  isPending: boolean;
}

const ActiveProjectContext = createContext<ActiveProjectValue | null>(null);

/**
 * Which project the whole dashboard is looking at.
 *
 * `?project=` is the single source of truth, so a view can be linked and the back button
 * works. localStorage only seeds it on first load. Selecting a project rescopes the page
 * the user is on; opening the project's own page is a separate action.
 */
export function ActiveProjectProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const params = useSearchParams();
  const projectsQuery = useProjectsQuery();
  const projects = projectsQuery.data ?? [];
  const fromUrl = params.get("project");

  // A remembered project that has since been deleted must not pin the dashboard to
  // something that no longer exists.
  const known = (id: string | null) =>
    id && projects.some((project) => project.id === id) ? id : null;

  function select(id: string, replace: boolean) {
    remember(id);
    // Built from the live URL, not the router hooks: during a navigation `pathname`
    // can still be the previous route, which would bounce the user back to it.
    const url = new URL(window.location.href);
    url.searchParams.set("project", id);
    const href = `${url.pathname}${url.search}`;
    if (replace) router.replace(href, { scroll: false });
    else router.push(href, { scroll: false });
  }

  // Seed the URL once projects are known. This navigates rather than setting state, so
  // the URL stays the only place the choice lives.
  useEffect(() => {
    if (known(fromUrl) || projects.length === 0) return;
    const target = known(remembered()) ?? projects[0]?.id;
    if (target) select(target, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fromUrl, projects]);

  const projectId = known(fromUrl) ?? projects[0]?.id ?? null;

  return (
    <ActiveProjectContext.Provider
      value={{
        projects,
        project: projects.find((project) => project.id === projectId),
        projectId,
        setProjectId: (id: string) => select(id, false),
        isPending: projectsQuery.isPending,
      }}
    >
      {children}
    </ActiveProjectContext.Provider>
  );
}

export function useActiveProject(): ActiveProjectValue {
  const value = useContext(ActiveProjectContext);
  if (!value) {
    throw new Error(
      "useActiveProject must be used inside ActiveProjectProvider",
    );
  }
  return value;
}

/** The active project id, or null outside the dashboard tree. Safe inside data hooks. */
export function useActiveProjectId(): string | null {
  return useContext(ActiveProjectContext)?.projectId ?? null;
}

/**
 * The active project's name, for copy that has to say which project something covers.
 * Null outside the dashboard tree and until the project list has answered, so every
 * caller needs wording that still reads without it.
 */
export function useActiveProjectName(): string | null {
  return useContext(ActiveProjectContext)?.project?.name ?? null;
}
