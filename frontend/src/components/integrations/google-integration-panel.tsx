"use client";

import { Button } from "@/components/tailgrids/core/button";
import { integrationsApi } from "@/services/api/integrations";
import { InfoTriangle } from "@tailgrids/icons";
import { useQuery } from "@tanstack/react-query";
import { GoogleConnectionCard } from "./google-connection-card";
import { IntegrationCardSkeleton } from "./integration-card-skeleton";
import { MessagePanel } from "./message-panel";
import { googleConnectionQueryKey } from "./query-keys";

function errorMessage(error: unknown, fallback: string) {
  return error instanceof Error && error.message ? error.message : fallback;
}

export function GoogleIntegrationPanel() {
  const connectionQuery = useQuery({
    queryKey: googleConnectionQueryKey,
    queryFn: integrationsApi.getGoogleConnection,
    retry: false,
    refetchOnWindowFocus: false,
  });

  if (connectionQuery.isPending) return <IntegrationCardSkeleton />;

  if (connectionQuery.isError) {
    return (
      <MessagePanel
        tone="error"
        icon={<InfoTriangle />}
        title="We could not load your integrations"
        description={errorMessage(
          connectionQuery.error,
          "Something went wrong while reading the connected Google account.",
        )}
      >
        <Button
          size="xl"
          onPress={() => void connectionQuery.refetch()}
          isDisabled={connectionQuery.isFetching}
        >
          {connectionQuery.isFetching ? "Retrying…" : "Try again"}
        </Button>
      </MessagePanel>
    );
  }

  const connection = connectionQuery.data;
  if (!connection) {
    return (
      <MessagePanel
        icon={<InfoTriangle />}
        title="No workspace data has been loaded yet"
        description="This build ships with a seeded demo workspace. Run the seed command in the backend to load the Google account, profiles and reviews."
      >
        <code className="rounded-md bg-background-gray-primary px-3 py-2 font-mono text-sm text-text-primary">
          uv run python -m app.seed
        </code>
      </MessagePanel>
    );
  }

  return <GoogleConnectionCard connection={connection} />;
}
