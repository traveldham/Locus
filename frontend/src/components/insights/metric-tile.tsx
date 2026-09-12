import { cn } from "@/utils/cn";
import { formatExact, formatHeadline } from "./chart-series";

interface MetricTileProps {
  label: string;
  /** `null` means Google reported nothing for this metric, which is not zero. */
  value: number | null;
  /** One short line under the value: what it covers, or why it is absent. */
  hint?: string;
  className?: string;
}

export function MetricTile({ label, value, hint, className }: MetricTileProps) {
  const headline = formatHeadline(value);
  const exact = formatExact(value);

  return (
    <div
      className={cn(
        "rounded-xl border border-card-border bg-card-background px-4 py-4",
        className,
      )}
    >
      <p className="text-[11px] font-medium tracking-[0.08em] text-text-tertiary uppercase">
        {label}
      </p>
      {headline === null ? (
        <p className="mt-1.5 text-lg leading-8 font-medium text-text-disable">Not reported</p>
      ) : (
        <p
          title={exact ?? undefined}
          className="mt-1.5 text-[28px] leading-9 font-semibold tracking-[-0.02em] text-text-primary"
        >
          {headline}
        </p>
      )}
      <p className="mt-1 text-xs leading-5 text-text-tertiary">
        {headline === null ? "Google returned no value for this range." : (hint ?? " ")}
      </p>
    </div>
  );
}
