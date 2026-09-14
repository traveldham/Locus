"use client";

import { BackLink } from "@/components/common/back-link";
import { DataField } from "@/components/common/data-field";
import { EmptyState } from "@/components/common/empty-state";
import { ErrorState } from "@/components/common/error-state";
import { LinkButton } from "@/components/common/link-button";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { Button } from "@/components/tailgrids/core/button";
import { Skeleton } from "@/components/tailgrids/core/skeleton";
import {
  useAttributeCatalogQuery,
  useLocationQuery,
} from "@/hooks/use-locations";
import { ApiError } from "@/services/api/client";
import type { LocationDetail } from "@/services/api/locations";
import { formatDateTime } from "@/utils/format-date";
import {
  Link1AngularRight,
  MapMarker5,
  PenToSquare,
  StarFat,
} from "@tailgrids/icons";
import { useState } from "react";
import {
  takeDraft,
  type DraftHandoff,
} from "@/components/recommendations/draft-handoff";
import { EditAppliedAlert } from "./edit-applied-alert";
import { LocationAttributesSection } from "./location-attributes-section";
import { LocationBusinessInfo } from "./location-business-info";
import { LocationChangeHistory } from "./location-change-history";
import { LocationEditForm, type AppliedEdit } from "./location-edit-form";
import { LocationGoogleStatus } from "./location-google-status";
import { LocationHoursSection } from "./location-hours-section";
import { BusinessProfilePreview } from "./preview/business-profile-preview";
import {
  LocationStatusChip,
  locationStatusKinds,
} from "./location-status-chip";

export function LocationDetailView({ locationId }: { locationId: string }) {
  const { data, isPending, isError, error, refetch, isFetching } =
    useLocationQuery(locationId);
  const isNotFound = error instanceof ApiError && error.status === 404;

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <BackLink href="/locations">All profiles</BackLink>

      {isPending ? <LocationDetailSkeleton /> : null}

      {!isPending && isError ? (
        <div className="mt-2 max-w-3xl">
          {isNotFound ? (
            <EmptyState
              icon={<MapMarker5 aria-hidden="true" focusable="false" />}
              title="Profile not found"
              description="This profile is no longer available to your organization. It may have been removed from the Google connection."
              actions={
                <LinkButton href="/locations" appearance="outline">
                  Back to profiles
                </LinkButton>
              }
            />
          ) : (
            <ErrorState
              title="We could not load this profile"
              description="The request to Locus did not complete. Check your connection, then try again."
              onRetry={() => void refetch()}
              isRetrying={isFetching}
            />
          )}
        </div>
      ) : null}

      {data ? <LocationProfile location={data} /> : null}
    </div>
  );
}

function LocationProfile({ location }: { location: LocationDetail }) {
  // A draft handed over from the audit opens the editor prefilled, once. It is read
  // during the first render, so the editor mounts already in the right mode.
  const [draft, setDraft] = useState<DraftHandoff | null>(() =>
    takeDraft(location.id),
  );
  const [showPreview, setShowPreview] = useState(() => draft === null);
  const [isEditing, setIsEditing] = useState(() => draft !== null);
  const [applied, setApplied] = useState<AppliedEdit | null>(null);
  const catalog = useAttributeCatalogQuery();

  function startEditing() {
    setShowPreview(false);
    setApplied(null);
    setIsEditing(true);
  }

  return (
    <>
      <PageHeader
        title={location.title}
        description={location.address ?? undefined}
        meta={locationStatusKinds(location, { includeVerified: true }).map(
          (kind) => (
            <LocationStatusChip key={kind} kind={kind} />
          ),
        )}
        actions={
          isEditing ? null : (
            <>
              {location.maps_uri ? (
                <LinkButton
                  href={location.maps_uri}
                  external
                  appearance="outline"
                >
                  <Link1AngularRight aria-hidden="true" focusable="false" />
                  Open in Google
                </LinkButton>
              ) : null}
              {location.new_review_uri ? (
                <LinkButton
                  href={location.new_review_uri}
                  external
                  appearance="outline"
                >
                  <StarFat aria-hidden="true" focusable="false" />
                  Ask for a review
                </LinkButton>
              ) : null}
              <Button type="button" size="xl" onPress={startEditing}>
                <PenToSquare aria-hidden="true" focusable="false" />
                Edit profile
              </Button>
              <LinkButton
                href={`/recommendations/${location.id}`}
                appearance="outline"
              >
                Audit this profile
              </LinkButton>
            </>
          )
        }
      />

      {applied ? (
        <div className="mt-6">
          <EditAppliedAlert
            result={applied}
            onDismiss={() => setApplied(null)}
          />
        </div>
      ) : null}

      {!isEditing ? (
        <div className="mt-6 flex flex-wrap gap-2" aria-label="Profile view">
          <Button
            type="button"
            size="xl"
            appearance={showPreview ? "fill" : "outline"}
            onPress={() => setShowPreview(true)}
          >
            Google-style preview
          </Button>
          <Button
            type="button"
            size="xl"
            appearance={!showPreview ? "fill" : "outline"}
            onPress={() => setShowPreview(false)}
          >
            Manage profile data
          </Button>
        </div>
      ) : null}

      {showPreview && !isEditing ? (
        <BusinessProfilePreview
          key={location.id}
          location={location}
          onEdit={startEditing}
        />
      ) : (
        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          <div className="flex min-w-0 flex-col gap-5 lg:col-span-2">
            {isEditing ? (
              <LocationEditForm
                key={location.id}
                location={location}
                draft={draft}
                onCancel={() => {
                  setDraft(null);
                  setIsEditing(false);
                }}
                onApplied={(result) => {
                  setDraft(null);
                  setIsEditing(false);
                  setApplied(result);
                }}
              />
            ) : (
              <>
                <LocationBusinessInfo location={location} />
                <LocationHoursSection
                  hours={location.hours_periods}
                  actions={
                    <Button
                      type="button"
                      variant="primary"
                      appearance="outline"
                      size="sm"
                      className="h-11 px-3.5"
                      onPress={startEditing}
                    >
                      <PenToSquare aria-hidden="true" focusable="false" />
                      Edit hours
                    </Button>
                  }
                />
              </>
            )}

            <SectionCard
              title="Address"
              icon={<MapMarker5 aria-hidden="true" focusable="false" />}
            >
              <dl className="grid gap-5 sm:grid-cols-2">
                <DataField label="Address" className="sm:col-span-2">
                  {location.address}
                </DataField>
                <DataField label="Place ID">
                  {location.place_id ? (
                    <span className="break-all tabular-nums">
                      {location.place_id}
                    </span>
                  ) : null}
                </DataField>
                <DataField label="Google profile name">
                  <span className="break-all">
                    {location.google_location_name}
                  </span>
                </DataField>
                <DataField label="Dataset profile ID">
                  {location.source_location_id ? (
                    <span className="tabular-nums">
                      {location.source_location_id}
                    </span>
                  ) : null}
                </DataField>
                <DataField label="Google resource name">
                  {location.google_resource_name ? (
                    <span className="break-all">
                      {location.google_resource_name}
                    </span>
                  ) : null}
                </DataField>
                <DataField label="Locality / region">
                  {[
                    location.locality,
                    location.administrative_area,
                    location.postal_code,
                    location.region_code,
                  ]
                    .filter(Boolean)
                    .join(", ") || null}
                </DataField>
                <DataField label="Coordinates">
                  {location.latitude !== null && location.longitude !== null ? (
                    <span className="tabular-nums">
                      {location.latitude}, {location.longitude}
                    </span>
                  ) : null}
                </DataField>
              </dl>
            </SectionCard>

            <LocationAttributesSection
              attributes={location.attributes}
              catalog={catalog.data?.items}
              isCatalogLoading={catalog.isPending}
            />
            <LocationChangeHistory locationId={location.id} />
          </div>

          <div className="flex min-w-0 flex-col gap-5">
            <LocationGoogleStatus location={location} />
            <SectionCard title="Sync" bodyClassName="px-5 py-4">
              <dl className="grid gap-5">
                <DataField label="Last synced">
                  {formatDateTime(location.last_synced_at)}
                </DataField>
                <DataField label="Added to Locus">
                  {formatDateTime(location.created_at)}
                </DataField>
                <DataField label="Last updated">
                  {formatDateTime(location.updated_at)}
                </DataField>
              </dl>
            </SectionCard>
          </div>
        </div>
      )}
    </>
  );
}

function LocationDetailSkeleton() {
  return (
    <div role="status" aria-label="Loading profile">
      <Skeleton className="h-8 w-72 max-w-full rounded-lg" />
      <Skeleton className="mt-3 h-4 w-96 max-w-full" />
      <div className="mt-4 flex gap-2">
        <Skeleton className="h-6 w-24 rounded-full" />
        <Skeleton className="h-6 w-28 rounded-full" />
      </div>
      <div className="mt-8 grid gap-5 lg:grid-cols-3">
        <div className="flex flex-col gap-5 lg:col-span-2">
          {[0, 1, 2].map((index) => (
            <div
              key={index}
              className="rounded-xl border border-card-border bg-card-background"
            >
              <div className="border-b border-card-border px-5 py-4">
                <Skeleton className="h-4 w-32" />
              </div>
              <div className="grid gap-5 px-5 py-5 sm:grid-cols-2">
                {[0, 1, 2, 3].map((field) => (
                  <div key={field}>
                    <Skeleton className="h-2.5 w-20" />
                    <Skeleton className="mt-2.5 h-3.5 w-40 max-w-full" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className="rounded-xl border border-card-border bg-card-background">
          <div className="border-b border-card-border px-5 py-4">
            <Skeleton className="h-4 w-28" />
          </div>
          <div className="flex flex-col gap-5 px-5 py-5">
            {[0, 1, 2, 3].map((field) => (
              <div
                key={field}
                className="flex items-center justify-between gap-4"
              >
                <Skeleton className="h-3.5 w-32" />
                <Skeleton className="h-6 w-24 rounded-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
