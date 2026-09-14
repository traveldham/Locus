"use client";

import { Button } from "@/components/tailgrids/core/button";
import { useDeleteProjectMutation } from "@/hooks/use-projects";
import { Trash1 } from "@tailgrids/icons";
import { useState } from "react";
import { ConfirmDialog } from "./confirm-dialog";

interface DeleteProjectButtonProps {
  projectId: string;
  projectName: string;
  locationCount: number;
}

/**
 * Deleting a project from the grid, without opening it first.
 *
 * The same confirmation and the same wording as the detail page's delete section: a
 * project is deleted from two places now, and the two must not disagree about what is
 * about to happen - especially about the locations, which survive and are the thing
 * people fear losing. There is no navigation afterwards because the grid is already
 * where the user is, and the mutation refreshes the lists on its own.
 */
export function DeleteProjectButton({
  projectId,
  projectName,
  locationCount,
}: DeleteProjectButtonProps) {
  const deleteProject = useDeleteProjectMutation(projectId);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  const locationsPhrase =
    locationCount === 1
      ? "The 1 profile in it"
      : `The ${locationCount} profiles in it`;

  function close() {
    if (deleteProject.isPending) return;
    setIsConfirmOpen(false);
    deleteProject.reset();
  }

  async function confirm() {
    // On failure the dialog stays open carrying the API's reason.
    const response = await deleteProject.mutateAsync().catch(() => null);
    if (response) setIsConfirmOpen(false);
  }

  return (
    <>
      <Button
        variant="danger"
        appearance="ghost"
        size="xl"
        iconOnly
        aria-label={`Delete ${projectName}`}
        // Above the card's stretched link, which otherwise covers the whole card.
        className="relative z-10 shrink-0"
        onPress={() => {
          deleteProject.reset();
          setIsConfirmOpen(true);
        }}
      >
        <Trash1 aria-hidden="true" focusable="false" />
      </Button>

      {isConfirmOpen ? (
        <ConfirmDialog
          title="Delete this project?"
          description={
            <>
              <p>
                <span className="font-medium text-text-secondary">
                  {projectName}
                </span>{" "}
                and its links to profiles will be deleted. This cannot be
                undone.
              </p>
              <p className="mt-3">
                {locationsPhrase} are not deleted. They stay in your workspace
                with their Google Business Profile data, and in any other
                project they belong to.
              </p>
            </>
          }
          confirmLabel="Delete project"
          pendingLabel="Deleting…"
          errorTitle="We could not delete this project"
          error={deleteProject.isError ? deleteProject.error : null}
          isPending={deleteProject.isPending}
          onConfirm={() => void confirm()}
          onCancel={close}
        />
      ) : null}
    </>
  );
}
