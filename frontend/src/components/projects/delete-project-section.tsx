"use client";

import { Button } from "@/components/tailgrids/core/button";
import { useDeleteProjectMutation } from "@/hooks/use-projects";
import { Trash1 } from "@tailgrids/icons";
import { useRouter } from "next/navigation";
import { useId, useState } from "react";
import { ConfirmDialog } from "./confirm-dialog";

interface DeleteProjectSectionProps {
  projectId: string;
  projectName: string;
  locationCount: number;
}

/** Kept apart from the rest of the page: this is the only irreversible action here. */
export function DeleteProjectSection({
  projectId,
  projectName,
  locationCount,
}: DeleteProjectSectionProps) {
  const headingId = useId();
  const router = useRouter();
  const deleteProject = useDeleteProjectMutation(projectId);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);

  const locationsPhrase =
    locationCount === 1 ? "The 1 location in it" : `The ${locationCount} locations in it`;

  function close() {
    if (deleteProject.isPending) return;
    setIsConfirmOpen(false);
    deleteProject.reset();
  }

  async function confirm() {
    const response = await deleteProject.mutateAsync().catch(() => null);
    // On failure the dialog stays open and shows the API's message.
    if (!response) return;
    setIsConfirmOpen(false);
    router.replace("/projects");
  }

  return (
    <section
      aria-labelledby={headingId}
      className="mt-12 rounded-xl border border-alert-danger-border bg-alert-danger-background px-5 py-5"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h2 id={headingId} className="text-sm font-semibold text-alert-danger-title">
            Delete this project
          </h2>
          <p className="mt-1.5 max-w-2xl text-sm leading-6 text-alert-danger-description">
            The project and its links to locations are removed. {locationsPhrase} stay in your
            workspace and in every other project they belong to.
          </p>
        </div>
        <Button
          variant="danger"
          size="xl"
          onPress={() => {
            deleteProject.reset();
            setIsConfirmOpen(true);
          }}
          className="shrink-0"
        >
          <Trash1 aria-hidden="true" focusable="false" />
          Delete project
        </Button>
      </div>

      {isConfirmOpen ? (
        <ConfirmDialog
          title="Delete this project?"
          description={
            <>
              <p>
                <span className="font-medium text-text-secondary">{projectName}</span> and its
                links to locations will be deleted. This cannot be undone.
              </p>
              <p className="mt-3">
                {locationsPhrase} are not deleted. They stay in your workspace with their Google
                Business Profile data, and in any other project they belong to.
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
    </section>
  );
}
