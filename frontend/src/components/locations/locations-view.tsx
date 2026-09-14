"use client";

import { useActiveProject } from "@/contexts/active-project";

import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { PageHeader } from "@/components/common/page-header";
import { SampleDataNotice } from "@/components/common/sample-data-notice";
import { useLocationsQuery } from "@/hooks/use-locations";
import { LOCATIONS_MAX_PAGE_SIZE } from "@/services/api/locations";
import { MapMarker5 } from "@tailgrids/icons";
import { LocationsTable } from "./locations-table";
import { LocationsTableSkeleton } from "./locations-table-skeleton";

export function LocationsView() {
  const { project } = useActiveProject();
  const { data, isPending, isError, refetch, isFetching } = useLocationsQuery();
  const locations = data ?? [];
  const hasSampleData = locations.some(
    (location) => location.source === "fixture",
  );

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <PageHeader
        title="Profiles"
        description={
          project
            ? `The profiles in ${project.name}, exactly as they stand on Google.`
            : "Every business profile imported into this organization, exactly as it stands on Google."
        }
      />

      {hasSampleData ? <SampleDataNotice className="mt-6" /> : null}

      <div className="mt-8">
        {isPending ? <LocationsTableSkeleton /> : null}

        {!isPending && isError ? (
          <div className="max-w-3xl">
            <ErrorState
              title="We could not load your profiles"
              onRetry={() => void refetch()}
              isRetrying={isFetching}
            />
          </div>
        ) : null}

        {!isPending && !isError && locations.length === 0 ? (
          <EmptyState
            icon={<MapMarker5 aria-hidden="true" focusable="false" />}
            title="No profiles to show"
            description="This workspace has no profiles loaded yet. Check the Google Business Profile connection, or adjust your search if you narrowed the list."
            actions={
              <LinkButton href="/settings/integrations" appearance="outline">
                View integration
              </LinkButton>
            }
          />
        ) : null}

        {!isPending && !isError && locations.length > 0 ? (
          <>
            <LocationsTable locations={locations} />
            {locations.length === LOCATIONS_MAX_PAGE_SIZE ? (
              <p className="mt-3 text-xs leading-5 text-text-tertiary">
                Showing the first {LOCATIONS_MAX_PAGE_SIZE} locations. Search
                narrows what is listed here.
              </p>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}
