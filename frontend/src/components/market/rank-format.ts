import type { RankPoint } from "@/services/api/market";
import { formatDate } from "@/utils/format-date";
import { format, isValid, parseISO } from "date-fns";

/** Copy used everywhere a null position appears, so the wording never drifts. */
export const NOT_FOUND_LABEL = "Not found";

export function formatRank(rank: number | null) {
  return rank === null ? NOT_FOUND_LABEL : `#${rank}`;
}

/** Short axis form, "7 Jul". Falls back to the raw value rather than inventing one. */
export function formatWeek(weekStart: string) {
  const parsed = parseISO(weekStart);
  return isValid(parsed) ? format(parsed, "d MMM") : weekStart;
}

export function formatWeekLong(weekStart: string) {
  return formatDate(weekStart) ?? weekStart;
}

/** A point counts as not found only when the API says the business was not found. */
export function isNotFound(point: RankPoint) {
  return !point.found || point.rank_absolute === null;
}

export function localPackLabel(rankInLocalPack: number | null) {
  return rankInLocalPack === null
    ? "Outside the local pack"
    : `Local pack #${rankInLocalPack}`;
}
