"use client";

import { SectionCard } from "@/components/common/section-card";
import type { AttributeCatalogItem, LocationAttribute } from "@/services/api/locations";
import { Filter } from "@tailgrids/icons";

/** Attribute ids arrive as Google resource names such as "attributes/has_delivery". */
function attributeLabel(attributeId: string) {
  const segment = attributeId.split("/").filter(Boolean).pop() ?? attributeId;
  const words = segment.replace(/[_-]+/g, " ").trim();
  if (!words) return attributeId;
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function formatValue(value: unknown): string | null {
  if (value === null || value === undefined) return null;
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "string") return value.trim() || null;
  if (typeof value === "number") return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return null;
  }
}

export function LocationAttributesSection({
  attributes,
  catalog,
  isCatalogLoading = false,
}: {
  attributes: LocationAttribute[];
  catalog?: AttributeCatalogItem[];
  isCatalogLoading?: boolean;
}) {
  const valuesByName = new Map(
    attributes.map((attribute) => [attribute.attribute_id.replace(/^attributes\//, ""), attribute]),
  );
  const rows = catalog?.length
    ? catalog.map((item) => {
        const configured = valuesByName.get(item.attribute_name);
        return {
          attributeId: item.external_attribute_id,
          label: attributeLabel(item.attribute_name),
          group: item.attribute_group,
          category: item.applies_to_category,
          valueType: item.value_type.replaceAll("_", " "),
          configured: Boolean(configured),
          values: (configured?.values ?? []).map(formatValue).filter((value): value is string => value !== null),
        };
      })
    : attributes.map((attribute) => ({
        attributeId: attribute.attribute_id,
        label: attributeLabel(attribute.attribute_id),
        group: "profile",
        category: "",
        valueType: attribute.value_type.replaceAll("_", " "),
        configured: true,
        values: attribute.values.map(formatValue).filter((value): value is string => value !== null),
      }));
  rows.sort((a, b) => a.group.localeCompare(b.group) || a.label.localeCompare(b.label));

  return (
    <SectionCard
      title="Attributes"
      icon={<Filter aria-hidden="true" focusable="false" />}
      bodyClassName="px-5 py-4"
    >
      <p className="mb-4 text-sm leading-5 text-text-tertiary">
        {isCatalogLoading
          ? "Loading the available attribute catalog…"
          : `${rows.filter((row) => row.configured).length} of ${rows.length} available attributes configured.`}
      </p>
      {rows.length === 0 ? (
        <p className="text-sm leading-6 text-text-tertiary">
          No attributes are set on this Google profile.
        </p>
      ) : (
        <dl className="divide-y divide-card-border">
          {rows.map((row) => (
            <div
              key={row.attributeId}
              className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 py-2.5 first:pt-0 last:pb-0"
            >
              <dt className="min-w-0 text-sm font-medium break-words text-text-primary">
                {row.label}
                <span className="ml-2 text-[11px] font-normal tracking-wide text-text-tertiary uppercase">{row.valueType}</span>
                <span className="mt-0.5 block text-xs font-normal text-text-tertiary">{attributeLabel(row.group)}{row.category ? ` · ${row.category}` : ""}</span>
              </dt>
              <dd className="text-right text-sm text-text-secondary">
                {!row.configured ? (
                  <span className="text-text-disable">Not configured</span>
                ) : row.values.length === 0 ? (
                  <span className="text-text-disable">No value</span>
                ) : (
                  row.values.map((value, index) => (
                    <span key={`${row.attributeId}-${index}`} className="block break-words">
                      {value}
                    </span>
                  ))
                )}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </SectionCard>
  );
}
