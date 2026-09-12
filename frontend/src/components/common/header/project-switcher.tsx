"use client";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuHeader,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/tailgrids/core/dropdown";
import { Skeleton } from "@/components/tailgrids/core/skeleton";
import { useProjectsQuery } from "@/hooks/use-projects";
import { AltArrowDownIcon } from "@/utils/icon";
import { Folder1 } from "@tailgrids/icons";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { NewProjectDialog } from "@/components/projects/new-project-dialog";

const NEW_PROJECT_KEY = "__new_project__";

/**
 * Switches between projects from the header, so the sidebar does not need a Projects
 * entry. Falls back to the first project when the current route is not a project page.
 */
export function ProjectSwitcher() {
  const router = useRouter();
  const params = useParams<{ id?: string }>();
  const [isCreating, setIsCreating] = useState(false);
  const projectsQuery = useProjectsQuery();

  const projects = projectsQuery.data ?? [];
  const active = projects.find((project) => project.id === params?.id) ?? projects[0];

  if (projectsQuery.isPending) {
    return <Skeleton className="h-8 w-44 rounded-lg" />;
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label={active ? `Project: ${active.name}` : "Choose a project"}
          className="flex max-w-[16rem] items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm font-medium text-text-primary transition-colors hover:bg-background-gray-secondary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600"
        >
          <Folder1 aria-hidden="true" focusable="false" className="size-4 text-icon-tertiary" />
          <span className="truncate">{active ? active.name : "No project"}</span>
          <AltArrowDownIcon />
        </DropdownMenuTrigger>

        <DropdownMenuContent className="min-w-[15rem]">
          <DropdownMenuHeader>Projects</DropdownMenuHeader>

          {projects.map((project) => (
            <DropdownMenuItem
              key={project.id}
              id={project.id}
              textValue={project.name}
              onAction={() => router.push(`/projects/${project.id}`)}
            >
              <span className="flex w-full items-center justify-between gap-3">
                <span className="truncate">{project.name}</span>
                <span className="shrink-0 text-xs text-text-tertiary tabular-nums">
                  {project.location_count}
                </span>
              </span>
            </DropdownMenuItem>
          ))}

          <DropdownMenuSeparator />
          <DropdownMenuItem
            id={NEW_PROJECT_KEY}
            textValue="New project"
            onAction={() => setIsCreating(true)}
          >
            New project
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {isCreating ? <NewProjectDialog onOpenChange={setIsCreating} /> : null}
    </>
  );
}
