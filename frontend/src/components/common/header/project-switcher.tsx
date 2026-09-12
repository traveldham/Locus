"use client";

import { NewProjectDialog } from "@/components/projects/new-project-dialog";
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
import { Check, Folder1, Plus } from "@tailgrids/icons";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

/**
 * Switches between projects from the header, so the sidebar needs no Projects entry.
 * The active project comes from the URL, falling back to the first one so the control
 * still reads sensibly on pages that are not project-scoped.
 *
 * Everything inside the menu must be a React Aria collection child — MenuItem, Header or
 * Separator. A wrapping div or a bare <p> silently drops out of the collection and the
 * items render as plain text, so scrolling lives on the Menu itself.
 */
export function ProjectSwitcher() {
  const router = useRouter();
  const params = useParams<{ id?: string }>();
  const [isCreating, setIsCreating] = useState(false);
  const projectsQuery = useProjectsQuery();

  const projects = projectsQuery.data ?? [];
  const active = projects.find((project) => project.id === params?.id) ?? projects[0];

  if (projectsQuery.isPending) {
    return <Skeleton className="h-11 w-52 rounded-lg" />;
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger
          aria-label={active ? `Project: ${active.name}` : "Choose a project"}
          className="group flex min-h-11 max-w-[18rem] items-center gap-2.5 rounded-lg border border-border-primary bg-background-white-primary px-3 py-2 transition-colors outline-none hover:bg-background-gray-secondary focus-visible:ring-4 focus-visible:ring-input-primary-focus-border/20 focus-visible:ring-offset-1"
        >
          <Folder1
            aria-hidden="true"
            focusable="false"
            className="size-4 shrink-0 text-icon-tertiary"
          />
          <span className="truncate text-sm leading-5 font-medium text-text-primary">
            {active ? active.name : "No project yet"}
          </span>
          <AltArrowDownIcon className="shrink-0 text-icon-tertiary transition-transform duration-200 group-aria-expanded:-rotate-180" />
        </DropdownMenuTrigger>

        <DropdownMenuContent
          placement="bottom start"
          className="max-h-[26rem] w-80 overflow-y-auto p-0 shadow-3xl"
        >
          <DropdownMenuHeader className="border-b border-border-secondary-alt px-4 py-3 text-xs font-medium tracking-[0.08em] text-text-tertiary uppercase">
            Projects
          </DropdownMenuHeader>

          {projects.map((project) => (
            <DropdownMenuItem
              key={project.id}
              id={project.id}
              textValue={project.name}
              onAction={() => router.push(`/projects/${project.id}`)}
              className="mx-1.5 mt-1.5 w-auto cursor-pointer px-3 py-2.5"
            >
              <span className="flex size-4 shrink-0 items-center justify-center text-icon-secondary">
                {active?.id === project.id ? (
                  <Check aria-hidden="true" focusable="false" className="size-4" />
                ) : null}
              </span>
              <span className="flex min-w-0 flex-1 items-center justify-between gap-3">
                <span className="truncate leading-5 text-text-primary">{project.name}</span>
                <span className="shrink-0 text-xs text-text-tertiary tabular-nums">
                  {project.location_count === 1
                    ? "1 location"
                    : `${project.location_count} locations`}
                </span>
              </span>
            </DropdownMenuItem>
          ))}

          <DropdownMenuSeparator className="mt-1.5" />

          <DropdownMenuItem
            id="new-project"
            textValue="New project"
            onAction={() => setIsCreating(true)}
            className="m-1.5 w-auto cursor-pointer px-3 py-2.5"
          >
            <span className="flex size-4 shrink-0 items-center justify-center text-icon-secondary group-hover:text-text-primary">
              <Plus aria-hidden="true" focusable="false" className="size-4" />
            </span>
            <span className="leading-5 text-text-primary">New project</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {isCreating ? <NewProjectDialog onOpenChange={setIsCreating} /> : null}
    </>
  );
}
