import { ACTION_METRIC_KEYS, IMPRESSION_METRIC_KEYS } from "@/services/api/insights";
import { ACTION_SERIES } from "./chart-series";
import { MetricTile } from "./metric-tile";

/**
 * The one figure Google does not report directly: the four surface-and-device
 * impression totals added together. It is only shown when at least one of them
 * exists, and it never stands in for a missing part.
 */
function totalImpressions(totals: Record<string, number>) {
  if (typeof totals.impressions === "number") {
    return {
      value: totals.impressions,
      reportedParts: IMPRESSION_METRIC_KEYS.length,
    };
  }
  const parts = IMPRESSION_METRIC_KEYS.filter((key) => typeof totals[key] === "number");
  if (parts.length === 0) return { value: null, reportedParts: 0 };
  return {
    value: parts.reduce((sum, key) => sum + totals[key], 0),
    reportedParts: parts.length,
  };
}

export function PerformanceTotals({ totals }: { totals: Record<string, number> }) {
  const impressions = totalImpressions(totals);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
      <MetricTile
        label="Impressions"
        value={impressions.value}
        hint={
          impressions.reportedParts === IMPRESSION_METRIC_KEYS.length
            ? "Maps and Search, desktop and mobile"
            : `Sum of the ${impressions.reportedParts} of 4 surfaces Google reported`
        }
      />
      {ACTION_METRIC_KEYS.map((key) => {
        const spec = ACTION_SERIES.find((candidate) => candidate.key === key);
        return (
          <MetricTile
            key={key}
            label={spec?.label ?? key}
            value={typeof totals[key] === "number" ? totals[key] : null}
            hint="Total for this range"
          />
        );
      })}
    </div>
  );
}
