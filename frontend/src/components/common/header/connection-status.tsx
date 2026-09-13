"use client";

import { googleConnectionQueryKey } from "@/components/integrations/query-keys";
import { integrationsApi } from "@/services/api/integrations";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

export function ConnectionStatus() {
  const query = useQuery({
    queryKey: googleConnectionQueryKey,
    queryFn: integrationsApi.getGoogleConnection,
    staleTime: 30_000,
    retry: false,
  });
  const status = query.data?.status;
  const label = query.isPending
    ? "Checking…"
    : query.isError
      ? "Status unavailable"
      : !query.data
        ? "Not connected"
        : status === "active"
          ? "connected"
          : status === "needs_reauth"
            ? "Reconnect needed"
            : status === "revoked"
              ? "Disconnected"
              : "Connection error";
  const active = !query.isError && status === "active";

  return (
    <Link
      href="/settings/integrations"
      title="Google Business Profile integration details. This workspace uses demo data, not a live Search Console connection."
      className="inline-flex min-h-11 items-center gap-2 rounded-lg px-3 text-xs text-text-secondary transition-colors hover:bg-background-gray-secondary focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500 sm:text-sm"
    >
      <span
        aria-hidden="true"
        className={`size-2 shrink-0 rounded-full ${active ? "bg-badge-success-text" : "bg-text-tertiary"}`}
      />
      <span>Google account</span>
      <span
        className={active ? "text-badge-success-text" : "text-text-secondary"}
      >
        {label}
      </span>
      {active ? <span className="text-xs text-text-tertiary">Demo</span> : null}
    </Link>
  );
}
