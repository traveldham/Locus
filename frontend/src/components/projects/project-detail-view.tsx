"use client";

import { BackLink } from "@/components/common/back-link";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { PageHeader } from "@/components/common/page-header";
import { LocationsTableSkeleton } from "@/components/locations/locations-table-skeleton";
import {
  Alert,
  AlertContent,
  AlertDescription,
  AlertIndicator,
  AlertTitle,
} from "@/components/tailgrids/core/alert";
import { Badge } from "@/components/tailgrids/core/badge";
import { Button } from "@/components/tailgrids/core/button";
import { Skeleton } from "@/components/tailgrids/core/skeleton";
import {
  useProjectQuery,
  useUpdateProjectMutation,
} from "@/hooks/use-projects";
import { ApiError } from "@/services/api/client";
import { formatDate } from "@/utils/format-date";
import {
  BoxArchive1,
  Folder1,
  Pencil1,
  RefreshCircle1Clockwise,
} from "@tailgrids/icons";
import { useState } from "react";
import { apiErrorMessage } from "./errors";
import { DeleteProjectSection } from "./delete-project-section";
import { ProjectLocationsPanel } from "./project-locations-panel";
import { RenameProjectDialog } from "./rename-project-dialog";

export function ProjectDetailView({ projectId }: { projectId: string }) {
  const { data, isPending, isError, error, refetch, isFetching } =
    useProjectQuery(projectId);
  const changeStatus = useUpdateProjectMutation(projectId);

  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const isNotFound = error instanceof ApiError && error.status === 404;
  const created = data ? formatDate(data.created_at) : null;
  const isArchived = data?.status === "archived";

  async function toggleArchived() {
    if (!data || changeStatus.isPending) return;
    const nextStatus = data.status === "archived" ? "active" : "archived";
    setStatusMessage(null);
    const project = await changeStatus
      .mutateAsync({ status: nextStatus })
      .catch(() => null);
    // A failure leaves the badge as it was; the message below the header says why.
    if (!project) return;
    setStatusMessage(
      project.status === "archived"
        ? "This project is now archived."
        : "This project is active again.",
    );
  }

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <BackLink href="/projects">All projects</BackLink>

      {isPending ? (
        <div role="status" aria-label="Loading project">
          <Skeleton className="h-8 w-64 max-w-full rounded-lg" />
          <Skeleton className="mt-3 h-4 w-80 max-w-full" />
          <div className="mt-8">
            <LocationsTableSkeleton rows={5} />
          </div>
        </div>
      ) : null}

      {!isPending && isError ? (
        <div className="mt-2 max-w-3xl">
          {isNotFound ? (
            <EmptyState
              icon={<Folder1 aria-hidden="true" focusable="false" />}
              title="Project not found"
              description="This project no longer exists, or it is not part of your organization."
              actions={
                <LinkButton href="/projects" appearance="outline">
                  Back to projects
                </LinkButton>
              }
            />
          ) : (
            <ErrorState
              title="We could not load this project"
              onRetry={() => void refetch()}
              isRetrying={isFetching}
            />
          )}
        </div>
      ) : null}

      {data ? (
        <>
          <PageHeader
            title={data.name}
            description={data.slug}
            meta={
              <>
                <Badge color={isArchived ? "gray" : "success"} size="md">
                  {isArchived ? "Archived" : "Active"}
                </Badge>
                <span className="text-sm text-text-tertiary">
                  {data.location_count}{" "}
                  {data.location_count === 1 ? "profile" : "profiles"}
                </span>
                {created ? (
                  <span className="text-sm text-text-tertiary">
                    Created {created}
                  </span>
                ) : null}
              </>
            }
            actions={
              <>
                <Button
                  variant="primary"
                  appearance="outline"
                  size="xl"
                  onPress={() => setIsRenameOpen(true)}
                >
                  <Pencil1 aria-hidden="true" focusable="false" />
                  Edit business details
                  <span className="sr-only"> {data.name}</span>
                </Button>
                <Button
                  variant="primary"
                  appearance="outline"
                  size="xl"
                  onPress={() => void toggleArchived()}
                  isDisabled={changeStatus.isPending}
                >
                  {isArchived ? (
                    <RefreshCircle1Clockwise
                      aria-hidden="true"
                      focusable="false"
                    />
                  ) : (
                    <BoxArchive1 aria-hidden="true" focusable="false" />
                  )}
                  {changeStatus.isPending
                    ? isArchived
                      ? "Restoring…"
                      : "Archiving…"
                    : isArchived
                      ? "Restore project"
                      : "Archive project"}
                </Button>
              </>
            }
          />

          <div aria-live="polite">
            {statusMessage ? (
              <p className="mt-5 text-sm text-text-tertiary">{statusMessage}</p>
            ) : null}
          </div>

          {changeStatus.isError ? (
            <div className="mt-5 max-w-3xl">
              <Alert status="error" className="max-w-none">
                <AlertIndicator />
                <AlertContent>
                  <AlertTitle>
                    We could not change the status of this project
                  </AlertTitle>
                  <AlertDescription>
                    {apiErrorMessage(changeStatus.error, "Please try again.")}
                  </AlertDescription>
                </AlertContent>
              </Alert>
            </div>
          ) : null}

          {isArchived ? (
            <div className="mt-5 max-w-3xl">
              <Alert status="warning" className="max-w-none">
                <AlertIndicator />
                <AlertContent>
                  <AlertTitle>This project is archived</AlertTitle>
                  <AlertDescription>
                    Archiving marks a project as finished. Its profiles are
                    untouched and still available everywhere else in Locus.
                    Restore the project to mark it active again.
                  </AlertDescription>
                </AlertContent>
              </Alert>
            </div>
          ) : null}

          <section
            aria-label="Business details"
            className="mt-6 rounded-xl border border-card-border bg-card-background p-5"
          >
            <h2 className="text-lg font-semibold text-text-primary">
              Business details
            </h2>
            <dl className="mt-4 space-y-4 text-sm">
              <div>
                <dt className="font-medium text-text-primary">Website</dt>
                <dd className="mt-1 break-all text-text-secondary">
                  {data.website_url ? (
                    <a
                      href={data.website_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex min-h-11 items-center underline underline-offset-4"
                    >
                      {data.website_url}
                    </a>
                  ) : (
                    "Not supplied"
                  )}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-text-primary">Services</dt>
                <dd className="mt-2 text-text-secondary">
                  {data.services?.length ? (
                    <ul className="flex flex-wrap gap-2">
                      {data.services.map((service) => (
                        <li
                          key={service}
                          className="rounded-lg bg-background-gray-secondary px-3 py-2"
                        >
                          {service}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    "Not supplied"
                  )}
                </dd>
              </div>
              <div>
                <dt className="font-medium text-text-primary">Description</dt>
                <dd className="mt-1 max-w-3xl whitespace-pre-wrap break-words leading-6 text-text-secondary">
                  {data.description || "Not supplied"}
                </dd>
              </div>
            </dl>
          </section>

          <ProjectLocationsPanel
            projectId={projectId}
            projectName={data.name}
            locations={data.locations}
            onStatusMessage={setStatusMessage}
          />

          <DeleteProjectSection
            projectId={projectId}
            projectName={data.name}
            locationCount={data.location_count}
          />

          {isRenameOpen ? (
            <RenameProjectDialog
              projectId={projectId}
              currentName={data.name}
              business={data}
              onClose={() => setIsRenameOpen(false)}
              onRenamed={(name) =>
                setStatusMessage(`Business details saved for ${name}.`)
              }
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
