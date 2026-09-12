import { Skeleton } from "@/components/tailgrids/core/skeleton";

export function KeywordListSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div role="status" aria-label="Loading tracked keywords" className="flex flex-col gap-2">
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="flex min-h-11 items-center justify-between gap-3 px-3 py-2">
          <div className="min-w-0 flex-1">
            <Skeleton className="h-3.5 w-40 max-w-full" />
            <Skeleton className="mt-2 h-2.5 w-28 max-w-full" />
          </div>
          <Skeleton className="h-6 w-11 shrink-0 rounded-md" />
        </div>
      ))}
    </div>
  );
}

export function RankChartSkeleton() {
  return (
    <div role="status" aria-label="Loading rank history">
      <Skeleton className="h-3 w-64 max-w-full" />
      <Skeleton className="mt-4 h-72 w-full rounded-xl sm:h-80" />
      <div className="mt-4 flex flex-wrap gap-4">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
  );
}

export function MarketTableSkeleton({
  rows = 6,
  columns = 6,
  label = "Loading results",
}: {
  rows?: number;
  columns?: number;
  label?: string;
}) {
  return (
    <div role="status" aria-label={label} className="overflow-hidden rounded-lg border border-border-primary">
      <div className="flex items-center gap-6 border-b border-border-primary bg-background-gray-secondary px-5 py-4">
        {Array.from({ length: columns }, (_, index) => (
          <Skeleton key={index} className="h-3 w-20 max-w-full flex-1" />
        ))}
      </div>
      {Array.from({ length: rows }, (_, rowIndex) => (
        <div
          key={rowIndex}
          className="flex items-center gap-6 border-b border-border-primary px-5 py-5 last:border-b-0"
        >
          {Array.from({ length: columns }, (_, index) => (
            <Skeleton key={index} className="h-3.5 w-20 max-w-full flex-1" />
          ))}
        </div>
      ))}
    </div>
  );
}
