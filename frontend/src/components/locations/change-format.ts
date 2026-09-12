import type { LocationHoursPeriod } from "@/services/api/locations";
import { dayLabel, describePeriod, humanizeToken } from "./hours-model";

function isHoursPeriod(value: unknown): value is LocationHoursPeriod {
  return typeof value === "object" && value !== null && "open_day" in value;
}

function isAttributeValue(value: unknown): value is { attribute_id: string; values?: unknown[] } {
  return typeof value === "object" && value !== null && "attribute_id" in value;
}

/**
 * Render one side of a profile change as readable lines.
 *
 * Scalar fields arrive as strings, but hours and attributes arrive as arrays of objects.
 * React cannot render those, and raw JSON would be unreadable to the person approving the
 * edit anyway — so they are formatted the way the rest of the app formats them.
 *
 * Returns null for an absent value so callers can show their own "Not set" treatment.
 */
export function describeChangeValue(value: unknown): string | null {
  if (value === null || value === undefined || value === "") return null;
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);

  if (Array.isArray(value)) {
    if (value.length === 0) return null;
    return value
      .map((item) => {
        if (isHoursPeriod(item)) return `${dayLabel(item.open_day)} ${describePeriod(item)}`;
        if (isAttributeValue(item)) {
          const values = Array.isArray(item.values) ? item.values.join(", ") : "";
          const label = humanizeToken(item.attribute_id);
          return values ? `${label}: ${values}` : label;
        }
        return typeof item === "string" ? item : JSON.stringify(item);
      })
      .join("\n");
  }

  return JSON.stringify(value);
}
