import { format, isValid, parseISO } from "date-fns";

function toDate(value: string | null | undefined) {
  if (!value) return null;
  const parsed = parseISO(value);
  return isValid(parsed) ? parsed : null;
}

/** "12 Sep 2026", or null when the API did not provide a usable value. */
export function formatDate(value: string | null | undefined) {
  const date = toDate(value);
  return date ? format(date, "d MMM yyyy") : null;
}

/** "12 Sep 2026, 2:32 PM", or null when the API did not provide a usable value. */
export function formatDateTime(value: string | null | undefined) {
  const date = toDate(value);
  return date ? format(date, "d MMM yyyy, h:mm a") : null;
}
