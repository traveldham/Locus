import { Skeleton } from "@/components/tailgrids/core/skeleton";

const COLUMN_WIDTHS = ["w-40", "w-56", "w-32", "w-16", "w-28", "w-24"];

export function LocationsTableSkeleton({ rows = 6 }: { rows?: number }) {
  return (
    <div role="status" aria-label="Loading profiles" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Skeleton className="h-11 w-full rounded-lg sm:max-w-sm" />
        <Skeleton className="h-4 w-28" />
      </div>
      <div className="overflow-hidden rounded-lg border border-border-primary">
        <div className="flex items-center gap-6 border-b border-border-primary bg-background-gray-secondary px-5 py-4">
          {COLUMN_WIDTHS.map((width, column) => (
            <Skeleton key={column} className={`h-3 ${width} max-w-full`} />
          ))}
        </div>
        {Array.from({ length: rows }, (_, index) => (
          <div
            key={index}
            className="flex items-center gap-6 border-b border-border-primary px-5 py-5 last:border-b-0"
          >
            {COLUMN_WIDTHS.map((width, column) => (
              <Skeleton key={column} className={`h-3.5 ${width} max-w-full`} />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
