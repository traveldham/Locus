import { Skeleton } from "@/components/tailgrids/core/skeleton";

export function IntegrationCardSkeleton() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="rounded-xl border border-card-border bg-card-background"
    >
      <span className="sr-only">Loading your Google connection</span>
      <div className="flex gap-4 border-b border-card-border p-5 sm:gap-5 sm:p-6">
        <Skeleton className="size-11 shrink-0 rounded-xl" />
        <div className="min-w-0 flex-1 space-y-2.5 pt-1">
          <Skeleton className="h-4 w-48 max-w-full" />
          <Skeleton className="h-3 w-full max-w-md" />
        </div>
      </div>
      <div className="space-y-3 p-5 sm:p-6">
        <Skeleton className="h-3 w-56 max-w-full" />
        <Skeleton className="h-3 w-full max-w-lg" />
        <Skeleton className="h-3 w-full max-w-sm" />
        <Skeleton className="mt-5 h-11 w-64 max-w-full rounded-lg" />
      </div>
    </div>
  );
}
