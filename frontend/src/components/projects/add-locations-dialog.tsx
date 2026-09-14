"use client";

import { ErrorState } from "@/components/common/error-state";
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
import { useAllLocationsQuery } from "@/hooks/use-locations";
import { useAddProjectLocationsMutation } from "@/hooks/use-projects";
import { cn } from "@/utils/cn";
import { Search1 } from "@tailgrids/icons";
import Link from "next/link";
import { useMemo, useState, type FormEvent } from "react";
import { apiErrorMessage } from "./errors";

interface AddLocationsDialogProps {
  projectId: string;
  projectName: string;
  /** The locations already linked, so the picker only offers the rest. */
  memberIds: readonly string[];
  onClose: () => void;
  onAdded: (addedCount: number) => void;
}

export function AddLocationsDialog({
  projectId,
  projectName,
  memberIds,
  onClose,
  onAdded,
}: AddLocationsDialogProps) {
  const locationsQuery = useAllLocationsQuery();
  const addLocations = useAddProjectLocationsMutation(projectId);

  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<ReadonlySet<string>>(
    new Set<string>(),
  );

  const members = useMemo(() => new Set(memberIds), [memberIds]);
  const available = useMemo(
    () =>
      (locationsQuery.data ?? []).filter(
        (location) => !members.has(location.id),
      ),
    [locationsQuery.data, members],
  );

  const query = search.trim().toLowerCase();
  const visible = useMemo(
    () =>
      query
        ? available.filter((location) =>
            [location.title, location.address, location.store_code]
              .filter((value): value is string => Boolean(value))
              .some((value) => value.toLowerCase().includes(query)),
          )
        : available,
    [available, query],
  );

  const isSubmittable = selected.size > 0 && !addLocations.isPending;

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isSubmittable) return;

    const locationIds = [...selected];
    // A failure keeps the dialog open with the same locations still ticked.
    const detail = await addLocations
      .mutateAsync(locationIds)
      .catch(() => null);
    if (!detail) return;

    onAdded(locationIds.length);
    onClose();
  }

  return (
    <Backdrop
      isOpen
      isDismissable={!addLocations.isPending}
      onOpenChange={(isOpen) => {
        if (!isOpen) onClose();
      }}
    >
      <Dialog
        className="flex max-h-[min(90vh,46rem)] w-full max-w-2xl flex-col overflow-hidden p-0"
        showCloseButton={false}
      >
        <form onSubmit={handleSubmit} className="flex min-h-0 flex-col">
          <DialogHeader className="border-b border-card-border px-6 py-5">
            <DialogTitle>Add profiles</DialogTitle>
            <p className="text-sm leading-6 text-text-tertiary">
              Choose which of your workspace profiles to add to{" "}
              <span className="font-medium text-text-secondary">
                {projectName}
              </span>
              . A profile can sit in more than one project, so adding it here
              does not remove it from anywhere else.
            </p>
          </DialogHeader>

          <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto px-6 py-5">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <p className="text-sm text-text-tertiary" aria-live="polite">
                {selected.size} selected
              </p>
              {selected.size > 0 ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onPress={() => setSelected(new Set<string>())}
                  isDisabled={addLocations.isPending}
                  className="h-11 px-3"
                >
                  Clear selection
                </Button>
              ) : null}
            </div>

            <div className="mt-3">
              {locationsQuery.isPending ? <LocationPickerSkeleton /> : null}

              {!locationsQuery.isPending && locationsQuery.isError ? (
                <ErrorState
                  title="We could not load your profiles"
                  description="The list of profiles did not load, so there is nothing to pick from yet."
                  onRetry={() => void locationsQuery.refetch()}
                  isRetrying={locationsQuery.isFetching}
                />
              ) : null}

              {!locationsQuery.isPending &&
              !locationsQuery.isError &&
              available.length === 0 ? (
                <div className="rounded-lg border border-dashed border-card-border px-4 py-5">
                  <p className="text-sm font-medium text-text-primary">
                    Nothing left to add
                  </p>
                  <p className="mt-1.5 text-sm leading-6 text-text-tertiary">
                    Every profile in your workspace is already in this project.
                  </p>
                  <Link
                    href="/locations"
                    className="mt-2 inline-flex min-h-11 items-center text-sm font-medium text-text-primary underline decoration-border-secondary-alt underline-offset-4 hover:decoration-current focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                  >
                    Browse profiles
                  </Link>
                </div>
              ) : null}

              {!locationsQuery.isPending &&
              !locationsQuery.isError &&
              available.length > 0 ? (
                <div className="rounded-lg border border-card-border">
                  <div className="relative border-b border-card-border p-2">
                    <Search1
                      aria-hidden="true"
                      focusable="false"
                      className="pointer-events-none absolute top-1/2 left-5 size-4 -translate-y-1/2 text-icon-tertiary"
                    />
                    <input
                      type="search"
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      aria-label="Search profiles to add"
                      placeholder="Search name, address or store code"
                      className="h-11 w-full rounded-md border-0 bg-transparent pr-3 pl-9 text-sm text-text-primary placeholder:text-input-placeholder-text focus:ring-0 focus:outline-2 focus:-outline-offset-2 focus:outline-primary-500"
                    />
                  </div>

                  <div className="scrollbar-thin max-h-64 overflow-y-auto p-1.5">
                    {visible.length === 0 ? (
                      <p className="px-3 py-6 text-center text-sm text-text-tertiary">
                        No profile outside this project matches “
                        {search.trim()}”.
                      </p>
                    ) : (
                      <ul>
                        {visible.map((location) => {
                          const isSelected = selected.has(location.id);
                          return (
                            <li key={location.id}>
                              <Checkbox
                                isSelected={isSelected}
                                onChange={() => toggle(location.id)}
                                isDisabled={addLocations.isPending}
                                className={cn(
                                  "flex min-h-11 w-full items-center gap-3 rounded-md px-2.5 py-2 text-left transition",
                                  isSelected
                                    ? "bg-background-gray-secondary"
                                    : "hover:bg-background-gray-secondary",
                                )}
                              >
                                <span className="min-w-0 flex-1">
                                  <span className="block truncate text-sm font-medium text-text-primary">
                                    {location.title}
                                  </span>
                                  <span className="mt-0.5 block truncate text-xs text-text-tertiary">
                                    {location.address ?? "Address not set"}
                                    {location.store_code
                                      ? ` · ${location.store_code}`
                                      : ""}
                                  </span>
                                </span>
                              </Checkbox>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </div>
                </div>
              ) : null}
            </div>

            {addLocations.isError ? (
              <p
                role="alert"
                className="mt-5 rounded-lg bg-alert-danger-background px-3 py-2.5 text-sm text-alert-danger-description"
              >
                {apiErrorMessage(
                  addLocations.error,
                  "We could not add those locations. Please try again.",
                )}
              </p>
            ) : null}
          </div>

          <DialogFooter className="border-t border-card-border px-6 py-4">
            <Button
              type="button"
              variant="primary"
              appearance="outline"
              size="xl"
              onPress={onClose}
              isDisabled={addLocations.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" size="xl" isDisabled={!isSubmittable}>
              {addLocations.isPending
                ? "Adding…"
                : selected.size === 0
                  ? "Add profiles"
                  : selected.size === 1
                    ? "Add 1 profile"
                    : `Add ${selected.size} profiles`}
            </Button>
          </DialogFooter>
        </form>
      </Dialog>
    </Backdrop>
  );
}

function LocationPickerSkeleton() {
  return (
    <div
      role="status"
      aria-label="Loading profiles"
      className="rounded-lg border border-card-border p-3"
    >
      {[0, 1, 2, 3].map((index) => (
        <div key={index} className="flex items-center gap-3 px-1 py-2.5">
          <Skeleton className="size-4 rounded" />
          <div className="flex-1">
            <Skeleton className="h-3.5 w-44 max-w-full" />
            <Skeleton className="mt-2 h-2.5 w-64 max-w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}
