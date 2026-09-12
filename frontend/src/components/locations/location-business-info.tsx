"use client";

import { DataField } from "@/components/common/data-field";
import { SectionCard } from "@/components/common/section-card";
import type { LocationDetail } from "@/services/api/locations";
import { formatDate } from "@/utils/format-date";
import { Buildings11, Link1AngularRight } from "@tailgrids/icons";
import type { ReactNode } from "react";
import { LocationStatusChip } from "./location-status-chip";

interface LocationBusinessInfoProps {
  location: LocationDetail;
  actions?: ReactNode;
}

/** The read-only view of every field the profile editor can change, plus its context. */
export function LocationBusinessInfo({ location, actions }: LocationBusinessInfoProps) {
  const primaryCategory =
    location.primary_category_display ??
    location.categories.find((category) => category.is_primary)?.display_name ??
    location.categories.find((category) => category.is_primary)?.category_name ??
    null;

  const otherCategories = location.categories.filter((category) => !category.is_primary);

  return (
    <SectionCard
      title="Business info"
      icon={<Buildings11 aria-hidden="true" focusable="false" />}
      actions={actions}
    >
      <dl className="grid gap-5 sm:grid-cols-2">
        <DataField label="Business name">{location.title}</DataField>
        <DataField label="Open status">
          {location.open_status ? <LocationStatusChip kind={location.open_status} /> : null}
        </DataField>
        <DataField label="Primary category">{primaryCategory}</DataField>
        <DataField label="Additional categories">
          {otherCategories.length > 0 ? (
            <span className="flex flex-wrap gap-1.5">
              {otherCategories.map((category) => (
                <span
                  key={category.category_name}
                  className="inline-flex items-center rounded-full bg-background-gray-secondary px-2.5 py-1 text-xs font-medium text-text-secondary"
                >
                  {category.display_name ?? category.category_name}
                </span>
              ))}
            </span>
          ) : null}
        </DataField>
        <DataField label="Phone">
          {location.phone_primary ? (
            <a
              href={`tel:${location.phone_primary.replace(/\s+/g, "")}`}
              className="inline-flex min-h-11 items-center font-medium underline decoration-border-secondary-alt underline-offset-4 hover:decoration-current focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
            >
              {location.phone_primary}
            </a>
          ) : null}
        </DataField>
        <DataField label="Store code">{location.store_code}</DataField>
        <DataField label="Website" className="sm:col-span-2">
          {location.website_uri ? (
            <a
              href={location.website_uri}
              target="_blank"
              rel="noreferrer noopener"
              className="inline-flex min-h-11 items-center gap-1.5 font-medium break-all underline decoration-border-secondary-alt underline-offset-4 hover:decoration-current focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500"
            >
              {location.website_uri}
              <Link1AngularRight
                aria-hidden="true"
                focusable="false"
                className="size-3.5 shrink-0"
              />
            </a>
          ) : null}
        </DataField>
        <DataField label="Description" className="sm:col-span-2">
          {location.description ? (
            <span className="block whitespace-pre-line">{location.description}</span>
          ) : null}
        </DataField>
        <DataField label="Opening date">{formatDate(location.opening_date)}</DataField>
      </dl>
    </SectionCard>
  );
}
