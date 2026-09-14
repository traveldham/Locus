import { GoogleIntegrationPanel } from "@/components/integrations/google-integration-panel";
import { IntegrationCardSkeleton } from "@/components/integrations/integration-card-skeleton";
import type { Metadata } from "next";
import { Suspense } from "react";

export const metadata: Metadata = {
  title: "Integrations",
  description: "The accounts Locus reads your profile data from.",
};

export default function IntegrationsSettingsPage() {
  return (
    <div className="px-5 py-8 lg:px-8 lg:py-10">
      <header className="max-w-3xl">
        <p className="text-xs font-medium tracking-[0.08em] text-text-tertiary uppercase">
          Settings
        </p>
        <h1 className="mt-2 text-[28px] leading-9 font-semibold tracking-[-0.03em] text-text-primary">
          Integrations
        </h1>
        <p className="mt-2 text-sm leading-6 text-text-tertiary">
          The accounts Locus reads your profile data from. One connection is shared across your
          organization and serves every project.
        </p>
      </header>

      <div className="mt-8 max-w-4xl">
        <Suspense fallback={<IntegrationCardSkeleton />}>
          <GoogleIntegrationPanel />
        </Suspense>
      </div>
    </div>
  );
}
