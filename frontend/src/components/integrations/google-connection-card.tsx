import { Alert, AlertContent, AlertDescription, AlertIndicator } from "@/components/tailgrids/core/alert";
import type { Connection, ConnectionStatus } from "@/services/api/integrations";
import { formatDateTime } from "@/utils/format-date";
import { IntegrationCardShell } from "./integration-card-shell";
import { StatusChip, type StatusChipTone } from "./status-chip";

const STATUS_PRESENTATION: Record<
  ConnectionStatus,
  { label: string; tone: StatusChipTone; notice: string | null }
> = {
  active: { label: "Connected", tone: "positive", notice: null },
  needs_reauth: {
    label: "Needs reconnecting",
    tone: "caution",
    notice: "Google needs this account to approve access again before profiles can be read.",
  },
  revoked: {
    label: "Access revoked",
    tone: "critical",
    notice: "Access to this Google account was revoked.",
  },
  error: {
    label: "Connection error",
    tone: "critical",
    notice: "This connection could not be used the last time it was tried.",
  },
};

function DetailRow({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-card-border px-4 py-3.5 last:border-b-0 sm:px-5 sm:odd:border-r sm:[&:nth-last-child(-n+2)]:border-b-0">
      <dt className="text-xs font-medium tracking-[0.08em] text-text-tertiary uppercase">{term}</dt>
      <dd className="mt-1.5 text-sm break-words text-text-primary">{children}</dd>
    </div>
  );
}

/** Read-only view of the connection this workspace was seeded with. */
export function GoogleConnectionCard({ connection }: { connection: Connection }) {
  const presentation = STATUS_PRESENTATION[connection.status];
  const connectedAt = formatDateTime(connection.connected_at);
  const lastSyncedAt = formatDateTime(connection.last_synced_at);

  return (
    <IntegrationCardShell
      title="Google Business Profile"
      description="The Google account this workspace reads profile data from. One connection serves every project."
      status={<StatusChip tone={presentation.tone} label={presentation.label} />}
    >
      {presentation.notice && (
        <Alert status={connection.status === "needs_reauth" ? "warning" : "error"} className="mb-5 max-w-none">
          <AlertIndicator />
          <AlertContent>
            <AlertDescription>{presentation.notice}</AlertDescription>
          </AlertContent>
        </Alert>
      )}

      <dl className="grid grid-cols-1 overflow-hidden rounded-lg border border-card-border sm:grid-cols-2">
        <DetailRow term="Google account">
          <span className="font-medium">{connection.google_account_email}</span>
        </DetailRow>
        <DetailRow term="Connected">
          {connectedAt ?? <span className="text-text-tertiary">Not recorded</span>}
        </DetailRow>
        <DetailRow term="Last synced">
          {lastSyncedAt ?? <span className="text-text-tertiary">Not synced yet</span>}
        </DetailRow>
        <DetailRow term="Access granted">
          {connection.scopes.length > 0 ? (
            <span className="flex flex-wrap gap-1.5">
              {connection.scopes.map((scope) => (
                <StatusChip
                  key={scope}
                  tone="neutral"
                  showDot={false}
                  label={scope.split("/").pop() || scope}
                  title={scope}
                />
              ))}
            </span>
          ) : (
            <span className="text-text-tertiary">None reported</span>
          )}
        </DetailRow>
      </dl>
    </IntegrationCardShell>
  );
}
