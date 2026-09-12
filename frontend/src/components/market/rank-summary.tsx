import type { RankPoint } from "@/services/api/market";
import { formatRank, formatWeekLong, isNotFound, NOT_FOUND_LABEL } from "./rank-format";

function Stat({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-lg border border-card-border bg-background-gray-secondary px-3.5 py-3">
      <dt className="text-xs leading-4 font-medium text-text-tertiary">{label}</dt>
      <dd className="mt-1 text-lg leading-6 font-semibold text-text-primary">{value}</dd>
      {detail ? (
        <dd className="mt-0.5 text-xs leading-4 text-text-tertiary">{detail}</dd>
      ) : null}
    </div>
  );
}

/**
 * Every figure here is read straight off the points the API returned — nothing is
 * projected, compared against an unreturned value, or filled in when it is missing.
 */
export function RankSummary({ points }: { points: RankPoint[] }) {
  if (points.length === 0) return null;

  const latest = points[points.length - 1];
  const found = points.filter((point) => !isNotFound(point));
  const ranks = found.map((point) => point.rank_absolute as number);
  const bestRank = ranks.length > 0 ? Math.min(...ranks) : null;
  const localPackWeeks = points.filter((point) => point.rank_in_local_pack !== null).length;
  const notFoundWeeks = points.length - found.length;

  return (
    <dl className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      <Stat
        label="Latest week"
        value={isNotFound(latest) ? NOT_FOUND_LABEL : formatRank(latest.rank_absolute)}
        detail={`Week of ${formatWeekLong(latest.week_start)}`}
      />
      <Stat
        label="Best position"
        value={bestRank === null ? NOT_FOUND_LABEL : formatRank(bestRank)}
        detail={
          bestRank === null ? "Not found in any week shown" : `Across ${points.length} weeks`
        }
      />
      <Stat
        label="Weeks in local pack"
        value={`${localPackWeeks} of ${points.length}`}
        detail="Top three map results"
      />
      <Stat
        label="Weeks not found"
        value={`${notFoundWeeks} of ${points.length}`}
        detail="No result for this keyword"
      />
    </dl>
  );
}
