import { Skeleton } from "@/components/tailgrids/core/skeleton";

function CardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-card-border bg-card-background p-5">
      {children}
    </div>
  );
}

export function PerformanceSkeleton() {
  return (
    <div role="status" aria-label="Loading performance" className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }, (_, index) => (
          <CardShell key={index}>
            <Skeleton className="h-2.5 w-20" />
            <Skeleton className="mt-4 h-6 w-16" />
            <Skeleton className="mt-3 h-2.5 w-24" />
          </CardShell>
        ))}
      </div>
      {Array.from({ length: 2 }, (_, index) => (
        <CardShell key={index}>
          <Skeleton className="h-4 w-40" />
          <Skeleton className="mt-6 h-56 w-full rounded-lg" />
          <Skeleton className="mt-5 h-2.5 w-64 max-w-full" />
        </CardShell>
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 8, label }: { rows?: number; label: string }) {
  return (
    <div role="status" aria-label={label}>
      <CardShell>
        <Skeleton className="h-4 w-40" />
        <div className="mt-5 flex flex-col gap-3">
          {Array.from({ length: rows }, (_, index) => (
            <div key={index} className="flex items-center justify-between gap-4">
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-3 w-16" />
            </div>
          ))}
        </div>
      </CardShell>
    </div>
  );
}

export function CardGridSkeleton({ cards = 4 }: { cards?: number }) {
  return (
    <div
      role="status"
      aria-label="Loading photo coverage"
      className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      {Array.from({ length: cards }, (_, index) => (
        <CardShell key={index}>
          <Skeleton className="h-4 w-40" />
          <Skeleton className="mt-5 h-8 w-20" />
          <Skeleton className="mt-5 h-3 w-full rounded-full" />
          <Skeleton className="mt-5 h-3 w-32" />
          <Skeleton className="mt-3 h-3 w-28" />
        </CardShell>
      ))}
    </div>
  );
}
