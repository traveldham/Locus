"use client";

import { SectionCard } from "@/components/common/section-card";
import type { LocationAttribute } from "@/services/api/locations";
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

export function LocationAttributesSection({ attributes }: { attributes: LocationAttribute[] }) {
  const rows = attributes
    .map((attribute) => ({
      attributeId: attribute.attribute_id,
      label: attributeLabel(attribute.attribute_id),
      values: attribute.values
        .map(formatValue)
        .filter((value): value is string => value !== null),
    }))
    .sort((a, b) => a.label.localeCompare(b.label));

  return (
    <SectionCard
      title="Attributes"
      icon={<Filter aria-hidden="true" focusable="false" />}
      bodyClassName="px-5 py-4"
    >
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
              </dt>
              <dd className="text-right text-sm text-text-secondary">
                {row.values.length === 0 ? (
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
