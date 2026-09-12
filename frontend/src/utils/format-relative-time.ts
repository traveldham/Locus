import { formatDistanceToNowStrict, isValid, parseISO } from "date-fns";

/** "2 days ago", or null when the API did not provide a usable value. */
export function formatRelativeTime(value: string | null | undefined) {
  if (!value) return null;
  const parsed = parseISO(value);
  return isValid(parsed) ? formatDistanceToNowStrict(parsed, { addSuffix: true }) : null;
}
