"use client";

import { NotSet } from "@/components/common/data-field";
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
import { Skeleton } from "@/components/tailgrids/core/skeleton";
import { Spinner } from "@/components/tailgrids/core/spinner";
import type { EditPreview, FieldChange } from "@/services/api/locations";
import { ArrowRight } from "@tailgrids/icons";
import { describeChangeValue } from "./change-format";
import { describeEditError } from "./edit-error";
import { editFieldLabel } from "./edit-fields";

interface EditPreviewDialogProps {
  locationTitle: string;
  preview: EditPreview | null;
  isLoadingPreview: boolean;
  previewError: unknown;
  isApplying: boolean;
  applyError: unknown;
  onRetryPreview: () => void;
  onBack: () => void;
  onConfirm: () => void;
}

/**
 * The consent step. Everything shown here comes from the API's own dry run against
 * Google, so the person confirming sees the same diff the server will send.
 */
export function EditPreviewDialog({
  locationTitle,
  preview,
  isLoadingPreview,
  previewError,
  isApplying,
  applyError,
  onRetryPreview,
  onBack,
  onConfirm,
}: EditPreviewDialogProps) {
  const fieldErrors = preview ? Object.entries(preview.field_errors) : [];
  const hasChanges = (preview?.changes.length ?? 0) > 0;
  const canConfirm = Boolean(preview?.valid) && hasChanges && !isLoadingPreview && !isApplying;

  return (
    <Backdrop isOpen isDismissable={!isApplying} onOpenChange={(open) => !open && onBack()}>
      <Dialog
        className="flex max-h-[min(90vh,46rem)] w-full max-w-2xl flex-col overflow-hidden p-0"
        showCloseButton={false}
      >
        <DialogHeader className="border-b border-card-border px-6 py-5">
          <DialogTitle>Review changes before they go live</DialogTitle>
          <p className="text-sm leading-6 text-text-tertiary">
            Confirming updates the Google Business Profile for{" "}
            <span className="font-medium text-text-secondary">{locationTitle}</span>. The
            changes below are published to Google Search and Maps.
          </p>
        </DialogHeader>

        <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto px-6 py-5">
          <div aria-live="polite" aria-busy={isLoadingPreview}>
            {isLoadingPreview ? <PreviewSkeleton /> : null}

            {!isLoadingPreview && previewError ? (
              <PreviewErrorAlert
                error={previewError}
                fallbackTitle="We could not check these changes"
                onRetry={onRetryPreview}
              />
            ) : null}

            {!isLoadingPreview && !previewError && preview ? (
              <>
                {fieldErrors.length > 0 ? (
                  <Alert status="error" className="mb-5 max-w-none">
                    <AlertIndicator />
                    <AlertContent>
                      <AlertTitle>
                        {fieldErrors.length === 1
                          ? "One field needs attention"
                          : `${fieldErrors.length} fields need attention`}
                      </AlertTitle>
                      <AlertDescription>
                        <ul className="space-y-1.5">
                          {fieldErrors.map(([field, message]) => (
                            <li key={field}>
                              <span className="font-medium">
                                {preview.changes.find((change) => change.field === field)?.label ??
                                  editFieldLabel(field)}
                                :
                              </span>{" "}
                              {message}
                            </li>
                          ))}
                        </ul>
                      </AlertDescription>
                    </AlertContent>
                  </Alert>
                ) : null}

                {hasChanges ? (
                  <>
                    <h3 className="text-[11px] font-medium tracking-[0.08em] text-text-tertiary uppercase">
                      {preview.changes.length === 1
                        ? "1 change"
                        : `${preview.changes.length} changes`}
                    </h3>
                    <ul className="mt-2.5 space-y-2.5">
                      {preview.changes.map((change) => (
                        <ChangeRow key={change.field} change={change} />
                      ))}
                    </ul>
                  </>
                ) : (
                  <div className="rounded-lg border border-dashed border-card-border px-4 py-6 text-center">
                    <p className="text-sm font-medium text-text-primary">Nothing to update</p>
                    <p className="mt-1.5 text-sm leading-6 text-text-tertiary">
                      This profile already matches what you entered, so there is nothing to
                      send to Google.
                    </p>
                  </div>
                )}
              </>
            ) : null}

            {applyError ? (
              <div className="mt-5">
                <PreviewErrorAlert
                  error={applyError}
                  fallbackTitle="We could not apply this change"
                />
              </div>
            ) : null}
          </div>
        </div>

        <DialogFooter className="border-t border-card-border px-6 py-4 sm:items-center sm:justify-between">
          <Button
            type="button"
            variant="primary"
            appearance="outline"
            size="xl"
            onPress={onBack}
            isDisabled={isApplying}
          >
            Back to editing
          </Button>
          <Button type="button" size="xl" onPress={onConfirm} isDisabled={!canConfirm}>
            {isApplying ? (
              <span aria-hidden="true" className="flex size-5 shrink-0 items-center justify-center">
                <Spinner size="sm" className="size-5" />
              </span>
            ) : null}
            {isApplying ? "Updating Google…" : "Confirm and update Google"}
          </Button>
        </DialogFooter>
      </Dialog>
    </Backdrop>
  );
}

function ChangeRow({ change }: { change: FieldChange }) {
  return (
    <li className="rounded-lg border border-card-border bg-background-gray-secondary/40 px-4 py-3">
      <p className="text-[11px] font-medium tracking-[0.08em] text-text-tertiary uppercase">
        {change.label}
      </p>
      <div className="mt-2 grid gap-2 sm:grid-cols-[1fr_auto_1fr] sm:items-start sm:gap-3">
        <ChangeValue caption="Current" value={change.current} />
        <ArrowRight
          aria-hidden="true"
          focusable="false"
          className="hidden size-4 shrink-0 self-center text-icon-tertiary sm:block"
        />
        <ChangeValue caption="New" value={change.proposed} emphasis />
      </div>
    </li>
  );
}

function ChangeValue({
  caption,
  value,
  emphasis = false,
}: {
  caption: string;
  value: unknown;
  emphasis?: boolean;
}) {
  const text = describeChangeValue(value);
  return (
    <div className="min-w-0">
      <p className="text-xs text-text-tertiary">{caption}</p>
      <p
        className={
          emphasis
            ? "mt-0.5 text-sm leading-6 font-medium break-words whitespace-pre-line text-text-primary"
            : "mt-0.5 text-sm leading-6 break-words whitespace-pre-line text-text-secondary"
        }
      >
        {text === null ? <NotSet /> : text}
      </p>
    </div>
  );
}

function PreviewErrorAlert({
  error,
  fallbackTitle,
  onRetry,
}: {
  error: unknown;
  fallbackTitle: string;
  onRetry?: () => void;
}) {
  const { title, description } = describeEditError(error, fallbackTitle);

  return (
    <Alert status="error" className="max-w-none">
      <AlertIndicator />
      <AlertContent>
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>{description}</AlertDescription>
        {onRetry ? (
          <Button type="button" size="xl" variant="danger" appearance="outline" onPress={onRetry}>
            Try again
          </Button>
        ) : null}
      </AlertContent>
    </Alert>
  );
}

function PreviewSkeleton() {
  return (
    <div role="status" aria-label="Checking these changes with Google">
      {[0, 1, 2].map((index) => (
        <div
          key={index}
          className="mb-2.5 rounded-lg border border-card-border px-4 py-3 last:mb-0"
        >
          <Skeleton className="h-2.5 w-24" />
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Skeleton className="h-3.5 w-40 max-w-full" />
            <Skeleton className="h-3.5 w-32 max-w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
