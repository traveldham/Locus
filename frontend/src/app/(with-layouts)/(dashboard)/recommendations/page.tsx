"use client";

import { ErrorState } from "@/components/common/error-state";
import { PageHeader } from "@/components/common/page-header";
import { LocationDirectory } from "@/components/recommendations/location-directory";
import { useActiveProject } from "@/contexts/active-project";
import { useAuditDirectory } from "@/hooks/use-recommendations";

export default function LocationsIndexPage() {
  const { project, projectId } = useActiveProject();
  const directory = useAuditDirectory(projectId);

  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <PageHeader
        title="Location audits"
        description={
          project
            ? `Profiles in ${project.name}. Each is audited on its own — open one to see its score, issues and the stored records behind them.`
            : "Each business profile is audited on its own. Open one to see its score, issues and the stored records behind them."
        }
      />
      <div className="mt-6">
        {directory.isPending ? (
          <p role="status" className="text-text-secondary">
            Loading locations…
          </p>
        ) : directory.error ? (
          <ErrorState
            title="We could not load your locations"
            onRetry={() => void directory.refetch()}
          />
        ) : (
          <LocationDirectory
            rows={directory.data?.items ?? []}
            benchmark={directory.data?.benchmark}
          />
        )}
      </div>
    </div>
  );
}
