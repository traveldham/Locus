"use client";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/tailgrids/core/button";
import { useAllLocationsQuery } from "@/hooks/use-locations";
import { useProjectsQuery } from "@/hooks/use-projects";
import { Folder1, Plus } from "@tailgrids/icons";
import { useState } from "react";
import { NewProjectDialog } from "./new-project-dialog";
import { ProjectCard } from "./project-card";
import { ProjectsGridSkeleton } from "./projects-grid-skeleton";

export function ProjectsView() {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const projectsQuery = useProjectsQuery();
  const locationsQuery = useAllLocationsQuery();

  const projects = projectsQuery.data ?? [];
  const importedCount = locationsQuery.data?.length ?? 0;
  const hasImportedLocations = importedCount > 0;
  // The empty state depends on whether any locations have loaded, so it waits for both
  // queries rather than flashing the wrong next step.
  const isLoading =
    projectsQuery.isPending ||
    (projects.length === 0 && locationsQuery.isPending);

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <PageHeader
        title="Projects"
        description="A project is a named set of profiles you work on together. A profile can belong to as many projects as you need."
        actions={
          <Button size="xl" onPress={() => setIsDialogOpen(true)}>
            <Plus aria-hidden="true" focusable="false" />
            New project
          </Button>
        }
      />

      <div className="mt-8">
        {isLoading ? <ProjectsGridSkeleton /> : null}

        {!isLoading && projectsQuery.isError ? (
          <div className="max-w-3xl">
            <ErrorState
              title="We could not load your projects"
              onRetry={() => void projectsQuery.refetch()}
              isRetrying={projectsQuery.isFetching}
            />
          </div>
        ) : null}

        {!isLoading && !projectsQuery.isError && projects.length === 0 ? (
          hasImportedLocations ? (
            <EmptyState
              icon={<Folder1 aria-hidden="true" focusable="false" />}
              title="No projects yet"
              description={`Your organization has ${importedCount} imported ${
                importedCount === 1 ? "profile" : "profiles"
              }. Group the ones you work on together into your first project.`}
              actions={
                <>
                  <Button size="xl" onPress={() => setIsDialogOpen(true)}>
                    <Plus aria-hidden="true" focusable="false" />
                    New project
                  </Button>
                  <LinkButton href="/locations" appearance="outline">
                    Browse profiles
                  </LinkButton>
                </>
              }
            />
          ) : (
            <EmptyState
              icon={<Folder1 aria-hidden="true" focusable="false" />}
              title="No profiles to group yet"
              description="Projects are built from the business profiles in your workspace. None have loaded yet, so there is nothing to group — you can still create an empty project and add profiles to it later."
              actions={
                <>
                  <Button size="xl" onPress={() => setIsDialogOpen(true)}>
                    Create an empty project
                  </Button>
                  <LinkButton
                    href="/settings/integrations"
                    appearance="outline"
                  >
                    View integration
                  </LinkButton>
                </>
              }
            />
          )
        ) : null}

        {!isLoading && !projectsQuery.isError && projects.length > 0 ? (
          <>
            <p className="mb-4 text-sm text-text-tertiary" aria-live="polite">
              {projects.length} {projects.length === 1 ? "project" : "projects"}
            </p>
            <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {projects.map((project) => (
                <li key={project.id} className="flex">
                  <ProjectCard project={project} />
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </div>

      {isDialogOpen ? (
        <NewProjectDialog onOpenChange={setIsDialogOpen} />
      ) : null}
    </div>
  );
}
