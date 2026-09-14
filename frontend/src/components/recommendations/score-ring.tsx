import { cn } from "@/utils/cn";
import { GRADE_LABEL, TONE_STROKE, TONE_TEXT, scoreTone } from "./audit-format";
import type { HealthScore } from "@/services/api/recommendations";

interface ScoreRingProps {
  score: number | null;
  grade: HealthScore["grade"];
  size?: number;
  label?: string;
  className?: string;
}

/** The headline score. An unscored audit shows a dash, never a zero. */
export function ScoreRing({
  score,
  grade,
  size = 132,
  label,
  className,
}: ScoreRingProps) {
  const tone = scoreTone(score);
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const filled = score === null ? 0 : (score / 100) * circumference;

  return (
    <div className={cn("flex items-center gap-4", className)}>
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          role="img"
          aria-label={
            score === null
              ? "Health score not evaluated"
              : `Health score ${score} out of 100, ${GRADE_LABEL[grade]}`
          }
        >
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            strokeWidth={stroke}
            className="stroke-card-border"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${filled} ${circumference}`}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            className={cn(
              "motion-safe:transition-[stroke-dasharray] motion-safe:duration-500",
              TONE_STROKE[tone],
            )}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={cn(
              "text-[32px] leading-9 font-semibold tracking-[-0.03em] tabular-nums",
              TONE_TEXT[tone],
            )}
          >
            {score ?? "—"}
          </span>
          <span className="text-[11px] text-text-tertiary">of 100</span>
        </div>
      </div>
      <div className="min-w-0">
        <p className={cn("text-sm font-semibold", TONE_TEXT[tone])}>
          {GRADE_LABEL[grade]}
        </p>
        {label ? (
          <p className="mt-1 text-xs leading-5 text-text-tertiary">{label}</p>
        ) : null}
      </div>
    </div>
  );
}

interface ScoreBarProps {
  score: number | null;
  className?: string;
}

/** Inline score used in dense rows where a ring would not fit. */
export function ScoreBar({ score, className }: ScoreBarProps) {
  const tone = scoreTone(score);
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div
        className="h-1.5 w-full min-w-16 overflow-hidden rounded-full bg-background-gray-secondary"
        role="presentation"
      >
        <div
          className={cn("h-full rounded-full", TONE_FILL_SAFE[tone])}
          style={{ width: `${score ?? 0}%` }}
        />
      </div>
      <span
        className={cn(
          "w-8 shrink-0 text-right text-sm font-medium",
          TONE_TEXT[tone],
        )}
      >
        {score ?? "—"}
      </span>
    </div>
  );
}

const TONE_FILL_SAFE = {
  success: "bg-badge-success-text",
  warning: "bg-badge-warning-text",
  error: "bg-badge-error-text",
  muted: "bg-text-disable",
} as const;
