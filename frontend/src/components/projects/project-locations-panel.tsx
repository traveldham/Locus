"use client";

import { NotSet } from "@/components/common/data-field";
import { EmptyState } from "@/components/common/empty-state";
import { Button } from "@/components/tailgrids/core/button";
import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRoot,
  TableRow,
} from "@/components/tailgrids/core/table";
import { useRemoveProjectLocationMutation } from "@/hooks/use-projects";
import type { LocationSummary } from "@/services/api/locations";
import { MapMarker5, Plus, Trash1 } from "@tailgrids/icons";
import Link from "next/link";
import { useId, useState } from "react";
import { AddLocationsDialog } from "./add-locations-dialog";
import { ConfirmDialog } from "./confirm-dialog";

interface ProjectLocationsPanelProps {
  projectId: string;
  projectName: string;
  locations: LocationSummary[];
  onStatusMessage: (message: string) => void;
}

export function ProjectLocationsPanel({
  projectId,
  projectName,
  locations,
  onStatusMessage,
}: ProjectLocationsPanelProps) {
  const headingId = useId();
  const removeLocation = useRemoveProjectLocationMutation(projectId);

  const [isAddOpen, setIsAddOpen] = useState(false);
  const [pendingRemoval, setPendingRemoval] = useState<LocationSummary | null>(
    null,
  );

  function closeRemoval() {
    if (removeLocation.isPending) return;
    setPendingRemoval(null);
    removeLocation.reset();
  }

  async function confirmRemoval() {
    if (!pendingRemoval) return;
    const removed = pendingRemoval;
    const response = await removeLocation
      .mutateAsync(removed.id)
      .catch(() => null);
    // On failure the dialog stays open and shows what the API said.
    if (!response) return;
    setPendingRemoval(null);
    removeLocation.reset();
    onStatusMessage(`${removed.title} was removed from this project.`);
  }

  return (
    <section aria-labelledby={headingId} className="mt-9">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h2
            id={headingId}
            className="text-base leading-6 font-semibold tracking-[-0.015em] text-text-primary"
          >
            Locations in this project
          </h2>
          <p className="mt-1 text-sm text-text-tertiary" aria-live="polite">
            {locations.length}{" "}
            {locations.length === 1 ? "location" : "locations"}
          </p>
        </div>
        <Button size="xl" onPress={() => setIsAddOpen(true)}>
          <Plus aria-hidden="true" focusable="false" />
          Add locations
        </Button>
      </div>

      <div className="mt-4">
        {locations.length === 0 ? (
          <EmptyState
            icon={<MapMarker5 aria-hidden="true" focusable="false" />}
            title="No locations in this project"
            description="Add locations from your workspace to start working on them together. A location can belong to several projects at once."
            actions={
              <Button size="xl" onPress={() => setIsAddOpen(true)}>
                <Plus aria-hidden="true" focusable="false" />
                Add locations
              </Button>
            }
          />
        ) : (
          <TableRoot className="min-w-[44rem]">
            <TableHeader className="bg-background-gray-secondary">
              <TableRow>
                <TableHead className="w-[30%]">Location</TableHead>
                <TableHead className="w-[32%]">Address</TableHead>
                <TableHead className="w-[20%]">Primary category</TableHead>
                <TableHead className="w-[18%] text-right">
                  <span className="sr-only">Actions</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {locations.map((location) => (
                <TableRow
                  key={location.id}
                  className="transition hover:bg-background-gray-secondary"
                >
                  <TableCell className="py-2">
                    <Link
                      href={`/locations/${location.id}`}
                      className="inline-flex min-h-11 items-center text-sm font-semibold text-text-primary underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                    >
                      {location.title}
                    </Link>
                  </TableCell>
                  <TableCell className="py-2 text-text-secondary">
                    {location.address ? (
                      <span
                        className="block max-w-80 truncate"
                        title={location.address}
                      >
                        {location.address}
                      </span>
                    ) : (
                      <NotSet />
                    )}
                  </TableCell>
                  <TableCell className="py-2 text-text-secondary">
                    {location.primary_category_display ?? <NotSet />}
                  </TableCell>
                  <TableCell className="py-2 text-right">
                    <Button
                      variant="danger"
                      appearance="ghost"
                      size="xl"
                      onPress={() => {
                        removeLocation.reset();
                        setPendingRemoval(location);
                      }}
                      className="ml-auto"
                    >
                      <Trash1 aria-hidden="true" focusable="false" />
                      Remove
                      <span className="sr-only">
                        {" "}
                        {location.title} from this project
                      </span>
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </TableRoot>
        )}
      </div>

      {isAddOpen ? (
        <AddLocationsDialog
          projectId={projectId}
          projectName={projectName}
          memberIds={locations.map((location) => location.id)}
          onClose={() => setIsAddOpen(false)}
          onAdded={(count) =>
            onStatusMessage(
              count === 1
                ? "1 location was added to this project."
                : `${count} locations were added to this project.`,
            )
          }
        />
      ) : null}

      {pendingRemoval ? (
        <ConfirmDialog
          title="Remove this location from the project?"
          description={
            <>
              <p>
                <span className="font-medium text-text-secondary">
                  {pendingRemoval.title}
                </span>{" "}
                will no longer be part of{" "}
                <span className="font-medium text-text-secondary">
                  {projectName}
                </span>
                .
              </p>
              <p className="mt-3">
                The location itself is not deleted. It stays in your workspace,
                keeps its Google Business Profile data, and remains in any other
                project it belongs to. You can add it back to this project at
                any time.
              </p>
            </>
          }
          confirmLabel="Remove from project"
          pendingLabel="Removing…"
          errorTitle="We could not remove this location"
          error={removeLocation.isError ? removeLocation.error : null}
          isPending={removeLocation.isPending}
          onConfirm={() => void confirmRemoval()}
          onCancel={closeRemoval}
        />
      ) : null}
    </section>
  );
}
