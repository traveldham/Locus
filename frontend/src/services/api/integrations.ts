import { apiRequest } from "./client";

export type ConnectionStatus = "active" | "needs_reauth" | "revoked" | "error";

export interface Connection {
  id: string;
  google_account_email: string;
  status: ConnectionStatus;
  scopes: string[];
  connected_at: string;
  last_synced_at: string | null;
}

export const integrationsApi = {
  // Null when the workspace has not been seeded yet — the API returns no connection
  // rather than an error, so the caller must render that state instead of assuming one.
  getGoogleConnection: () =>
    apiRequest<Connection | null>("/integrations/google"),
};
