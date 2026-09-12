"use client";

import {
  Alert,
  AlertContent,
  AlertDescription,
  AlertIndicator,
  AlertTitle,
} from "@/components/tailgrids/core/alert";
import { Button } from "@/components/tailgrids/core/button";
import {
  Dialog,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/tailgrids/core/dialog";
import { Backdrop } from "@/components/tailgrids/core/overlay";
import { Spinner } from "@/components/tailgrids/core/spinner";
import type { ReactNode } from "react";
import { apiErrorMessage } from "./errors";

interface ConfirmDialogProps {
  title: string;
  /** Says plainly what the action does, and what it leaves alone. */
  description: ReactNode;
  confirmLabel: string;
  pendingLabel: string;
  errorTitle: string;
  error: unknown;
  isPending: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/** The shared confirmation step for the project actions that remove something. */
export function ConfirmDialog({
  title,
  description,
  confirmLabel,
  pendingLabel,
  errorTitle,
  error,
  isPending,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <Backdrop
      isOpen
      isDismissable={!isPending}
      onOpenChange={(isOpen) => {
        if (!isOpen) onCancel();
      }}
    >
      <Dialog className="w-full max-w-lg p-0" showCloseButton={false}>
        <DialogHeader className="px-6 pt-6">
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>

        <div className="px-6 pt-3 pb-1 text-sm leading-6 text-text-tertiary">{description}</div>

        {error ? (
          <div className="px-6 pt-4">
            <Alert status="error" className="max-w-none">
              <AlertIndicator />
              <AlertContent>
                <AlertTitle>{errorTitle}</AlertTitle>
                <AlertDescription>
                  {apiErrorMessage(error, "Please try again.")}
                </AlertDescription>
              </AlertContent>
            </Alert>
          </div>
        ) : null}

        <DialogFooter className="px-6 pt-5 pb-6">
          <Button
            type="button"
            variant="primary"
            appearance="outline"
            size="xl"
            onPress={onCancel}
            isDisabled={isPending}
          >
            Cancel
          </Button>
          <Button
            type="button"
            variant="danger"
            size="xl"
            onPress={onConfirm}
            isDisabled={isPending}
          >
            {isPending ? (
              <span aria-hidden="true" className="flex size-5 shrink-0 items-center justify-center">
                <Spinner size="sm" className="size-5" />
              </span>
            ) : null}
            {isPending ? pendingLabel : confirmLabel}
          </Button>
        </DialogFooter>
      </Dialog>
    </Backdrop>
  );
}
