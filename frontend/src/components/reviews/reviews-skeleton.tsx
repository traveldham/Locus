import { Skeleton } from "@/components/tailgrids/core/skeleton";

export function ReviewsSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div role="status" aria-label="Loading reviews" className="flex flex-col gap-3">
      {Array.from({ length: rows }, (_, index) => (
        <div
          key={index}
          className="rounded-xl border border-card-border bg-card-background p-4 sm:p-5"
        >
          <div className="flex items-center justify-between gap-4">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-3 w-20" />
          </div>
          <Skeleton className="mt-4 h-3.5 w-56 max-w-full" />
          <Skeleton className="mt-4 h-3 w-full" />
          <Skeleton className="mt-2.5 h-3 w-4/5 max-w-full" />
          <Skeleton className="mt-5 h-11 w-32 rounded-lg" />
        </div>
      ))}
    </div>
  );
}
