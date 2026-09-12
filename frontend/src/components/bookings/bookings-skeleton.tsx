import { Skeleton } from "@/components/tailgrids/core/skeleton";

const COLUMN_WIDTHS = ["w-32", "w-40", "w-36", "w-24", "w-20", "w-24", "w-28"];

export function BookingsSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div role="status" aria-label="Loading bookings" className="flex flex-col gap-4">
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
