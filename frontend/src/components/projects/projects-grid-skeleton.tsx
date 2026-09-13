import { Skeleton } from "@/components/tailgrids/core/skeleton";

export function ProjectsGridSkeleton({ cards = 6 }: { cards?: number }) {
  return (
    <div
      role="status"
      aria-label="Loading projects"
      className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"
    >
      {Array.from({ length: cards }, (_, index) => (
        <div
          key={index}
          className="rounded-xl border border-card-border bg-card-background p-5"
        >
          <div className="flex items-start justify-between gap-3">
            <Skeleton className="size-10 rounded-lg" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="mt-4 h-4 w-40 max-w-full" />
          <Skeleton className="mt-2.5 h-2.5 w-24" />
          <div className="mt-5 flex gap-8 border-t border-card-border pt-4">
            <div>
              <Skeleton className="h-2.5 w-16" />
              <Skeleton className="mt-2 h-3.5 w-8" />
            </div>
            <div>
              <Skeleton className="h-2.5 w-14" />
              <Skeleton className="mt-2 h-3.5 w-20" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
