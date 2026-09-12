"use client";

import { Button } from "@/components/tailgrids/core/button";
import {
  Dialog,
  DialogBody,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/tailgrids/core/dialog";

export interface RemoveReplyDialogProps {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  /** Named so it is unmistakable which review's reply is about to disappear. */
  reviewerName: string;
  locationTitle: string;
  onConfirm: () => void;
  isRemoving: boolean;
  error: string | null;
}

/**
 * Removing a reply is publicly visible, so it is confirmed. Only the reply goes:
 * Google provides no way for a business to remove the review itself.
 */
export function RemoveReplyDialog({
  isOpen,
  onOpenChange,
  reviewerName,
  locationTitle,
  onConfirm,
  isRemoving,
  error,
}: RemoveReplyDialogProps) {
  return (
    <Dialog isOpen={isOpen} onOpenChange={onOpenChange} showCloseButton={!isRemoving}>
      <DialogHeader>
        <DialogTitle>Remove your reply?</DialogTitle>
      </DialogHeader>
      <DialogBody className="space-y-3 leading-6">
        <p>
          Your reply to{" "}
          <span className="font-medium text-text-primary">{reviewerName}</span> at{" "}
          <span className="font-medium text-text-primary">{locationTitle}</span> will be taken
          down from Google. Anyone reading the review will see it without a response.
        </p>
        <p>
          The review itself stays published — Google gives businesses no way to remove a
          customer&rsquo;s review. You can write a new reply at any time.
        </p>
        {error ? (
          <p
            role="alert"
            className="rounded-lg bg-badge-error-background px-3 py-2 text-sm text-badge-error-text"
          >
            {error}
          </p>
        ) : null}
      </DialogBody>
      <DialogFooter>
        <Button
          size="xl"
          variant="primary"
          appearance="outline"
          onPress={() => onOpenChange(false)}
          isDisabled={isRemoving}
        >
          Keep reply
        </Button>
        <Button size="xl" variant="danger" onPress={onConfirm} isDisabled={isRemoving}>
          {isRemoving ? "Removing…" : "Remove reply"}
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
