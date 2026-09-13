import type { ScorePoint } from "@/services/api/recommendations";
import { cn } from "@/utils/cn";
import { TONE_STROKE, TONE_TEXT, scoreTone } from "./audit-format";

/** Health score over the last audits. Two points make a line; one makes a dot. */
export function ScoreTrend({ history }: { history: ScorePoint[] }) {
  const points = history.filter((p) => p.score !== null) as (ScorePoint & {
    score: number;
  })[];
  if (points.length < 2) {
    return (
      <p className="text-xs leading-5 text-text-tertiary">
        {points.length === 1
          ? "First scored audit. The trend appears after the next one."
          : "No scored audits yet."}
      </p>
    );
  }
  const width = 220;
  const height = 56;
  const pad = 6;
  const xs = points.map(
    (_, i) => pad + (i * (width - 2 * pad)) / (points.length - 1),
  );
  const ys = points.map(
    (p) => height - pad - (p.score / 100) * (height - 2 * pad),
  );
  const path = xs
    .map((x, i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${ys[i].toFixed(1)}`)
    .join(" ");
  const last = points[points.length - 1];
  const first = points[0];
  const delta = last.score - first.score;
  const tone = scoreTone(last.score);
  return (
    <div>
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Score trend across ${points.length} audits, from ${first.score} to ${last.score}`}
        className="max-w-full"
      >
        <path
          d={path}
          fill="none"
          strokeWidth={2}
          className={cn(TONE_STROKE[tone])}
        />
        {xs.map((x, i) => (
          <circle
            key={points[i].run_id}
            cx={x}
            cy={ys[i]}
            r={3}
            className={cn(
              "fill-current",
              TONE_TEXT[scoreTone(points[i].score)],
            )}
          />
        ))}
      </svg>
      <p className="mt-1 text-xs leading-5 text-text-tertiary">
        {points.length} audits ·{" "}
        <span
          className={cn(
            "font-medium",
            delta > 0 ? TONE_TEXT.success : delta < 0 ? TONE_TEXT.error : "",
          )}
        >
          {delta > 0 ? `+${delta}` : delta} since the first
        </span>
      </p>
    </div>
  );
}
