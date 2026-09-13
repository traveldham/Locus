"use client";

import { Button } from "@/components/tailgrids/core/button";
import {
  Dialog,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/tailgrids/core/dialog";
import { FieldLabel } from "@/components/tailgrids/core/field";
import { Input } from "@/components/tailgrids/core/input";
import { Backdrop } from "@/components/tailgrids/core/overlay";
import { TextField } from "@/components/tailgrids/core/text-field";
import { useUpdateProjectMutation } from "@/hooks/use-projects";
import { useState, type FormEvent } from "react";
import { apiErrorMessage } from "./errors";
import {
  PROJECT_NAME_MAX_LENGTH,
  PROJECT_NAME_MIN_LENGTH,
  projectNameError,
} from "./project-name";

interface RenameProjectDialogProps {
  projectId: string;
  currentName: string;
  onClose: () => void;
  onRenamed: (name: string) => void;
}

export function RenameProjectDialog({
  projectId,
  currentName,
  onClose,
  onRenamed,
}: RenameProjectDialogProps) {
  const rename = useUpdateProjectMutation(projectId);
  const [name, setName] = useState(currentName);
  const [wasSubmitted, setWasSubmitted] = useState(false);

  const validationError = projectNameError(name);
  const showValidationError = wasSubmitted && validationError !== null;
  const trimmed = name.trim();
  const isUnchanged = trimmed === currentName.trim();

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (rename.isPending) return;

    setWasSubmitted(true);
    if (validationError) return;

    if (isUnchanged) {
      onClose();
      return;
    }

    // A failure keeps the dialog open with what was typed still in the field.
    const project = await rename
      .mutateAsync({ name: trimmed })
      .catch(() => null);
    if (!project) return;

    onRenamed(project.name);
    onClose();
  }

  return (
    <Backdrop
      isOpen
      isDismissable={!rename.isPending}
      onOpenChange={(isOpen) => {
        if (!isOpen) onClose();
      }}
    >
      <Dialog className="w-full max-w-lg p-0" showCloseButton={false}>
        <form onSubmit={handleSubmit}>
          <DialogHeader className="px-6 pt-6">
            <DialogTitle>Rename project</DialogTitle>
            <p className="text-sm leading-6 text-text-tertiary">
              The web address of this project does not change, so existing links
              keep working. Its locations are not affected.
            </p>
          </DialogHeader>

          <div className="px-6 pt-5">
            <TextField
              value={name}
              onChange={setName}
              autoFocus
              invalid={showValidationError}
              disabled={rename.isPending}
              className="gap-1.5"
              aria-describedby={
                showValidationError
                  ? "rename-project-error"
                  : "rename-project-hint"
              }
            >
              <FieldLabel>Project name</FieldLabel>
              <Input className="h-11 w-full" />
              {showValidationError ? (
                <p
                  id="rename-project-error"
                  role="alert"
                  className="text-xs text-input-error"
                >
                  {validationError}
                </p>
              ) : (
                <p
                  id="rename-project-hint"
                  className="text-xs text-text-tertiary"
                >
                  Between {PROJECT_NAME_MIN_LENGTH} and{" "}
                  {PROJECT_NAME_MAX_LENGTH} characters.
                </p>
              )}
            </TextField>

            {rename.isError ? (
              <p
                role="alert"
                className="mt-4 rounded-lg bg-alert-danger-background px-3 py-2.5 text-sm text-alert-danger-description"
              >
                {apiErrorMessage(
                  rename.error,
                  "We could not rename this project. Please try again.",
                )}
              </p>
            ) : null}
          </div>

          <DialogFooter className="px-6 pt-5 pb-6">
            <Button
              type="button"
              variant="primary"
              appearance="outline"
              size="xl"
              onPress={onClose}
              isDisabled={rename.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" size="xl" isDisabled={rename.isPending}>
              {rename.isPending ? "Saving…" : "Save name"}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </Backdrop>
  );
}
