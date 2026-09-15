"use client";

import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { useActiveProjectId } from "@/contexts/active-project";
import { apiErrorMessage } from "@/components/projects/errors";
import { locationRoot } from "@/components/recommendations/audit-nav";
import {
  Alert,
  AlertContent,
  AlertDescription,
  AlertIndicator,
  AlertTitle,
} from "@/components/tailgrids/core/alert";
import { Badge } from "@/components/tailgrids/core/badge";
import { Button } from "@/components/tailgrids/core/button";
import { Checkbox } from "@/components/tailgrids/core/checkbox";
import {
  Dialog,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/tailgrids/core/dialog";
import { Backdrop } from "@/components/tailgrids/core/overlay";
import { Skeleton } from "@/components/tailgrids/core/skeleton";
import { Spinner } from "@/components/tailgrids/core/spinner";
import {
  useDemoProfilesQuery,
  useImportDemoProfilesMutation,
} from "@/hooks/use-demo-profiles";
import type {
  DemoProfile,
  DemoProfileGrade,
} from "@/services/api/demo-profiles";
import { cn } from "@/utils/cn";
import { CheckCircle1 } from "@tailgrids/icons";
import Link from "next/link";
import { useMemo, useState, type FormEvent, type ReactNode } from "react";

/** What one finished import left behind, as the alert on the profiles list reports it. */
export interface SampleImportOutcome {
  imported: number;
  skipped: number;
  locationIds: string[];
  /** The names that were sent, so the alert can say what arrived rather than only how many. */
  names: string[];
}

const GRADE_COLOR: Record<DemoProfileGrade, "error" | "warning"> = {
  poor: "error",
  fair: "warning",
};

function profileCount(count: number) {
  return count === 1 ? "1 profile" : `${count} profiles`;
}

interface ImportSampleProfilesDialogProps {
  onClose: () => void;
  onImported: (outcome: SampleImportOutcome) => void;
}

/**
 * The sample catalogue, as a picker.
 *
 * Every entry is a business with a real problem — unanswered reviews, collapsed search
 * visibility — so the row leads with that problem: it is what the profile will demonstrate
 * once it is audited. Everything not already in the organization starts ticked, so the
 * common case is one click.
 */
export function ImportSampleProfilesDialog({
  onClose,
  onImported,
}: ImportSampleProfilesDialogProps) {
  const projectId = useActiveProjectId();
  const catalogue = useDemoProfilesQuery();
  const importProfiles = useImportDemoProfilesMutation();

  // Null means "nothing chosen yet", which is what makes the default below possible.
  const [selection, setSelection] = useState<ReadonlySet<string> | null>(null);

  const items = useMemo(() => catalogue.data?.items ?? [], [catalogue.data]);
  const importable = useMemo(
    () => items.filter((item) => !item.imported),
    [items],
  );
  const defaultSelection = useMemo(
    () => new Set(importable.map((item) => item.key)),
    [importable],
  );
  const selected = selection ?? defaultSelection;

  const isPending = importProfiles.isPending;
  const isSubmittable = selected.size > 0 && !isPending;

  function toggle(key: string) {
    setSelection((current) => {
      const next = new Set(current ?? defaultSelection);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isSubmittable) return;

    const chosen = importable.filter((item) => selected.has(item.key));
    if (chosen.length === 0) return;

    // A failure keeps the dialog open with the same profiles still ticked, so the person
    // can read what the API objected to and press Import again.
    const result = await importProfiles
      // Imported into the project being viewed: the profiles list and the audit
      // directory are both project-scoped, so without this the new profiles would land
      // where neither of them looks and the import would appear to have done nothing.
      .mutateAsync({ keys: chosen.map((item) => item.key), projectId })
      .catch(() => null);
    if (!result) return;

    const byKey = new Map(chosen.map((item) => [item.key, item.name]));
    onImported({
      imported: result.imported.length,
      skipped: result.skipped.length,
      locationIds: result.imported.map((row) => row.location_id),
      // Only the ones that were really created, so the summary cannot name a profile
      // that was skipped as already present or is not in the catalogue any more.
      names: result.imported.map((row) => byKey.get(row.key) ?? row.key),
    });
    onClose();
  }

  return (
    <Backdrop
      isOpen
      isDismissable={!isPending}
      onOpenChange={(isOpen) => {
        if (!isOpen) onClose();
      }}
    >
      <Dialog
        className="flex max-h-[min(90vh,48rem)] w-full max-w-3xl flex-col overflow-hidden p-0"
        showCloseButton={false}
      >
        <form onSubmit={handleSubmit} className="flex min-h-0 flex-col">
          <DialogHeader className="border-b border-card-border px-6 py-5">
            <DialogTitle>Import sample profiles</DialogTitle>
            <p className="text-sm leading-6 text-text-tertiary">
              These are example businesses with real problems in their listings.
              Import the ones you want and audit them to see the findings and
              the drafts Locus writes for each.
            </p>
          </DialogHeader>

          <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto px-6 py-5">
            {catalogue.isPending ? <CataloguePickerSkeleton /> : null}

            {!catalogue.isPending && catalogue.isError ? (
              <ErrorState
                title="We could not load the sample profiles"
                description="The catalogue did not load, so there is nothing to pick from yet."
                onRetry={() => void catalogue.refetch()}
                isRetrying={catalogue.isFetching}
              />
            ) : null}

            {!catalogue.isPending &&
            !catalogue.isError &&
            items.length === 0 ? (
              <div className="rounded-lg border border-dashed border-card-border px-4 py-5">
                <p className="text-sm font-medium text-text-primary">
                  No sample profiles are available
                </p>
                <p className="mt-1.5 text-sm leading-6 text-text-tertiary">
                  This workspace has no sample catalogue to import from.
                </p>
              </div>
            ) : null}

            {!catalogue.isPending && !catalogue.isError && items.length > 0 ? (
              <>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm text-text-tertiary" aria-live="polite">
                    {importable.length === 0
                      ? "Every sample profile is already in your workspace"
                      : `${selected.size} of ${importable.length} selected`}
                  </p>
                  {importable.length > 0 ? (
                    <div className="flex flex-wrap items-center gap-1">
                      <Button
                        type="button"
                        variant="primary"
                        appearance="ghost"
                        size="sm"
                        onPress={() => setSelection(new Set(defaultSelection))}
                        isDisabled={
                          isPending || selected.size === importable.length
                        }
                        className="h-11 px-3"
                      >
                        Select all
                      </Button>
                      <Button
                        type="button"
                        variant="primary"
                        appearance="ghost"
                        size="sm"
                        onPress={() => setSelection(new Set<string>())}
                        isDisabled={isPending || selected.size === 0}
                        className="h-11 px-3"
                      >
                        Clear selection
                      </Button>
                    </div>
                  ) : null}
                </div>

                <ul className="mt-3 divide-y divide-card-border rounded-lg border border-card-border">
                  {items.map((profile) => (
                    <li key={profile.key}>
                      {profile.imported ? (
                        <ImportedRow profile={profile} />
                      ) : (
                        <SelectableRow
                          profile={profile}
                          isSelected={selected.has(profile.key)}
                          isDisabled={isPending}
                          onToggle={() => toggle(profile.key)}
                        />
                      )}
                    </li>
                  ))}
                </ul>
              </>
            ) : null}

            {importProfiles.isError ? (
              <div className="mt-5">
                <Alert status="error" className="max-w-none">
                  <AlertIndicator />
                  <AlertContent>
                    <AlertTitle>We could not import those profiles</AlertTitle>
                    <AlertDescription>
                      {apiErrorMessage(
                        importProfiles.error,
                        "The request to Locus did not complete. Your selection is still here, so you can try again.",
                      )}
                    </AlertDescription>
                  </AlertContent>
                </Alert>
              </div>
            ) : null}
          </div>

          <DialogFooter className="border-t border-card-border px-6 py-4">
            <Button
              type="button"
              variant="primary"
              appearance="outline"
              size="xl"
              onPress={onClose}
              isDisabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" size="xl" isDisabled={!isSubmittable}>
              {isPending ? (
                <span
                  aria-hidden="true"
                  className="flex size-5 shrink-0 items-center justify-center"
                >
                  <Spinner size="sm" className="size-5" />
                </span>
              ) : null}
              {isPending
                ? "Importing…"
                : selected.size === 0
                  ? "Import profiles"
                  : `Import ${profileCount(selected.size)}`}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </Backdrop>
  );
}

function SelectableRow({
  profile,
  isSelected,
  isDisabled,
  onToggle,
}: {
  profile: DemoProfile;
  isSelected: boolean;
  isDisabled: boolean;
  onToggle: () => void;
}) {
  return (
    <Checkbox
      isSelected={isSelected}
      onChange={onToggle}
      isDisabled={isDisabled}
      className={cn(
        "flex min-h-11 w-full items-start gap-3 px-4 py-3.5 text-left transition",
        isSelected
          ? "bg-background-gray-secondary"
          : "hover:bg-background-gray-secondary",
      )}
    >
      <ProfileSummary profile={profile} />
    </Checkbox>
  );
}

function ImportedRow({ profile }: { profile: DemoProfile }) {
  return (
    <div className="flex min-h-11 w-full items-start gap-3 px-4 py-3.5">
      <CheckCircle1
        aria-hidden="true"
        focusable="false"
        className="mt-0.5 size-4 shrink-0 text-icon-tertiary"
      />
      <ProfileSummary
        profile={profile}
        trailing={
          <span className="flex flex-wrap items-center gap-3">
            <Badge color="gray" size="sm">
              Already in your workspace
            </Badge>
            {profile.location_id ? (
              <Link
                href={locationRoot(profile.location_id)}
                className="inline-flex min-h-11 items-center text-sm font-medium text-text-primary underline decoration-border-secondary-alt underline-offset-4 hover:decoration-current focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
              >
                Open audit
                <span className="sr-only"> for {profile.name}</span>
              </Link>
            ) : null}
          </span>
        }
      />
    </div>
  );
}

function ProfileSummary({
  profile,
  trailing,
}: {
  profile: DemoProfile;
  trailing?: ReactNode;
}) {
  return (
    <span className="min-w-0 flex-1">
      <span className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
        <span className="text-sm font-medium text-text-primary">
          {profile.name}
        </span>
        <Badge color={GRADE_COLOR[profile.expected_grade]} size="sm">
          Expected grade: {profile.expected_grade}
        </Badge>
      </span>
      <span className="mt-0.5 block text-xs text-text-tertiary">
        {profile.industry} · {profile.city}
      </span>
      <span className="mt-1.5 block text-sm leading-6 text-text-secondary">
        {profile.headline_problem}
      </span>
      {trailing ? <span className="mt-2 block">{trailing}</span> : null}
    </span>
  );
}

function CataloguePickerSkeleton() {
  return (
    <div
      role="status"
      aria-label="Loading sample profiles"
      className="rounded-lg border border-card-border p-3"
    >
      {[0, 1, 2, 3].map((index) => (
        <div key={index} className="flex items-start gap-3 px-1 py-3">
          <Skeleton className="mt-1 size-4 rounded" />
          <div className="flex-1">
            <Skeleton className="h-3.5 w-48 max-w-full" />
            <Skeleton className="mt-2 h-2.5 w-36 max-w-full" />
            <Skeleton className="mt-2.5 h-3 w-72 max-w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

interface SampleImportResultAlertProps {
  outcome: SampleImportOutcome;
  /** Set when the list is scoped to a project, which changes where the new profiles are. */
  project?: { id: string; name: string };
  onDismiss: () => void;
}

/**
 * What the import did, and the step that follows it.
 *
 * Importing does not audit, so a list of new rows on its own shows nothing: this points
 * at the audit, which is the reason these profiles exist.
 */
export function SampleImportResultAlert({
  outcome,
  project,
  onDismiss,
}: SampleImportResultAlertProps) {
  const { imported, skipped, locationIds, names } = outcome;
  const nothingNew = imported === 0;
  const auditHref =
    locationIds.length === 1
      ? locationRoot(locationIds[0])
      : "/recommendations";

  return (
    <Alert status={nothingNew ? "info" : "success"} className="max-w-none">
      <AlertIndicator />
      <AlertContent>
        <AlertTitle>
          {nothingNew
            ? "Nothing new to import"
            : `${profileCount(imported)} imported`}
        </AlertTitle>
        <AlertDescription>
          {nothingNew ? (
            <p>
              Every profile you chose was already in your workspace, so nothing
              was added.
            </p>
          ) : (
            <>
              <p>
                {names.length > 0 ? `${names.join(", ")}. ` : ""}
                No audit has run on {imported === 1 ? "it" : "them"} yet — that
                is the step that finds the problems and drafts the fixes.
              </p>
              {skipped > 0 ? (
                <p className="mt-2">
                  {profileCount(skipped)} {skipped === 1 ? "was" : "were"}{" "}
                  already in your workspace and {skipped === 1 ? "was" : "were"}{" "}
                  skipped.
                </p>
              ) : null}
              {project ? (
                <p className="mt-2">
                  Added to {project.name}, so {imported === 1 ? "it is" : "they are"}{" "}
                  already in this list.
                </p>
              ) : null}
            </>
          )}
        </AlertDescription>
        <div className="flex flex-wrap items-center gap-2.5">
          {nothingNew ? null : (
            <LinkButton
              href={auditHref}
              variant="success"
              appearance="outline"
              size="xl"
            >
              {locationIds.length === 1 ? "Run its audit" : "Run an audit"}
            </LinkButton>
          )}
          <Button
            type="button"
            size="xl"
            variant={nothingNew ? "primary" : "success"}
            appearance="ghost"
            onPress={onDismiss}
          >
            Dismiss
          </Button>
        </div>
      </AlertContent>
    </Alert>
  );
}
