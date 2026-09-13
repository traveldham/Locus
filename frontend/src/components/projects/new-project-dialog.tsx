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
import { FieldLabel } from "@/components/tailgrids/core/field";
import { Input } from "@/components/tailgrids/core/input";
import { Backdrop } from "@/components/tailgrids/core/overlay";
import { Skeleton } from "@/components/tailgrids/core/skeleton";
import { TextField } from "@/components/tailgrids/core/text-field";
import { useAllLocationsQuery } from "@/hooks/use-locations";
import { useCreateProjectMutation } from "@/hooks/use-projects";
import { cn } from "@/utils/cn";
import { Search1 } from "@tailgrids/icons";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";
import {
  BusinessFields,
  businessPayload,
  emptyBusiness,
} from "./business-fields";
import {
  PROJECT_NAME_MAX_LENGTH,
  PROJECT_NAME_MIN_LENGTH,
  projectNameError,
} from "./project-name";

interface NewProjectDialogProps {
  onOpenChange: (isOpen: boolean) => void;
}

export function NewProjectDialog({ onOpenChange }: NewProjectDialogProps) {
  const router = useRouter();
  const locationsQuery = useAllLocationsQuery();
  const createProject = useCreateProjectMutation();

  const [name, setName] = useState("");
  const [business, setBusiness] = useState(emptyBusiness);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<ReadonlySet<string>>(
    new Set<string>(),
  );

  const locations = useMemo(
    () => locationsQuery.data ?? [],
    [locationsQuery.data],
  );
  const query = search.trim().toLowerCase();

  const visible = useMemo(
    () =>
      query
        ? locations.filter((location) =>
            [location.title, location.address, location.store_code]
              .filter((value): value is string => Boolean(value))
              .some((value) => value.toLowerCase().includes(query)),
          )
        : locations,
    [locations, query],
  );

  const trimmedName = name.trim();
  // The same 2 to 160 character rule the API enforces.
  const isSubmittable =
    projectNameError(name) === null && !createProject.isPending;

  function toggle(id: string) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectAllVisible() {
    setSelected((current) => {
      const next = new Set(current);
      for (const location of visible) next.add(location.id);
      return next;
    });
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isSubmittable) return;

    const locationIds = [...selected];
    const project = await createProject
      .mutateAsync({
        name: trimmedName,
        ...businessPayload(business),
        ...(locationIds.length > 0 ? { location_ids: locationIds } : {}),
      })
      .catch(() => null);

    if (!project) return;
    onOpenChange(false);
    router.push(`/projects/${project.id}`);
  }

  return (
    <Backdrop
      isOpen
      onOpenChange={onOpenChange}
      isDismissable={!createProject.isPending}
    >
      <Dialog className="flex max-h-[min(90vh,46rem)] w-full max-w-2xl flex-col overflow-hidden p-0">
        <form onSubmit={handleSubmit} className="flex min-h-0 flex-col">
          <DialogHeader className="border-b border-card-border px-6 py-5 pr-14">
            <DialogTitle>New project</DialogTitle>
            <p className="text-sm leading-6 text-text-tertiary">
              Add your business details, then choose its imported locations.
            </p>
          </DialogHeader>

          <div className="scrollbar-thin min-h-0 flex-1 overflow-y-auto px-6 py-5">
            <TextField
              value={name}
              onChange={setName}
              required
              autoFocus
              className="gap-1.5"
              aria-describedby="new-project-name-hint"
            >
              <FieldLabel>Business name</FieldLabel>
              <Input
                className="h-11 w-full"
                placeholder="For example, Brightpath Dental"
              />
              <p
                id="new-project-name-hint"
                className="text-xs text-text-tertiary"
              >
                Between {PROJECT_NAME_MIN_LENGTH} and {PROJECT_NAME_MAX_LENGTH}{" "}
                characters. You can rename a project later without affecting its
                locations.
              </p>
            </TextField>

            <BusinessFields
              value={business}
              onChange={setBusiness}
              disabled={createProject.isPending}
            />

            <div className="mt-7">
              <div className="flex flex-wrap items-end justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-text-primary">
                    Locations
                  </h3>
                  <p
                    className="mt-1 text-xs leading-5 text-text-tertiary"
                    aria-live="polite"
                  >
                    {selected.size} selected
                  </p>
                </div>
                {locations.length > 0 ? (
                  <div className="flex items-center gap-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onPress={selectAllVisible}
                      className="h-11 px-3"
                    >
                      Select all{query ? " shown" : ""}
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onPress={() => setSelected(new Set<string>())}
                      isDisabled={selected.size === 0}
                      className="h-11 px-3"
                    >
                      Clear
                    </Button>
                  </div>
                ) : null}
              </div>

              <div className="mt-3">
                {locationsQuery.isPending ? <LocationPickerSkeleton /> : null}

                {!locationsQuery.isPending && locationsQuery.isError ? (
                  <ErrorState
                    title="We could not load your locations"
                    description="You can still create the project and add locations once the list loads."
                    onRetry={() => void locationsQuery.refetch()}
                    isRetrying={locationsQuery.isFetching}
                  />
                ) : null}

                {!locationsQuery.isPending &&
                !locationsQuery.isError &&
                locations.length === 0 ? (
                  <div className="rounded-lg border border-dashed border-card-border px-4 py-5">
                    <p className="text-sm font-medium text-text-primary">
                      No locations have loaded yet
                    </p>
                    <p className="mt-1.5 text-sm leading-6 text-text-tertiary">
                      There is nothing to pick from right now. You can create
                      this project and add locations afterwards.
                    </p>
                    <Link
                      href="/settings/integrations"
                      className="mt-2 inline-flex min-h-11 items-center text-sm font-medium text-text-primary underline decoration-border-secondary-alt underline-offset-4 hover:decoration-current focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
                    >
                      View integration
                    </Link>
                  </div>
                ) : null}

                {!locationsQuery.isPending &&
                !locationsQuery.isError &&
                locations.length > 0 ? (
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
                        aria-label="Search locations to add"
                        placeholder="Search name, address or store code"
                        className="h-11 w-full rounded-md border-0 bg-transparent pr-3 pl-9 text-sm text-text-primary placeholder:text-input-placeholder-text focus:ring-0 focus:outline-2 focus:-outline-offset-2 focus:outline-primary-500"
                      />
                    </div>

                    <div className="scrollbar-thin max-h-64 overflow-y-auto p-1.5">
                      {visible.length === 0 ? (
                        <p className="px-3 py-6 text-center text-sm text-text-tertiary">
                          No location matches “{search.trim()}”.
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
            </div>

            {createProject.isError ? (
              <p
                role="alert"
                className="mt-5 rounded-lg bg-alert-danger-background px-3 py-2.5 text-sm text-alert-danger-description"
              >
                {createProject.error instanceof Error
                  ? createProject.error.message
                  : "We could not create that project. Please try again."}
              </p>
            ) : null}
          </div>

          <DialogFooter className="border-t border-card-border px-6 py-4">
            <Button
              type="button"
              variant="primary"
              appearance="outline"
              size="xl"
              onPress={() => onOpenChange(false)}
              isDisabled={createProject.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" size="xl" isDisabled={!isSubmittable}>
              {createProject.isPending ? "Creating…" : "Create project"}
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
      aria-label="Loading locations"
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
