import { apiRequest } from "./client";

/**
 * How the sample profile is expected to score once it is audited. The catalogue exists to
 * demonstrate the audit, so every entry is deliberately imperfect.
 */
export type DemoProfileGrade = "poor" | "fair";

/** One entry of the sample catalogue the API offers for import. */
export interface DemoProfile {
  key: string;
  name: string;
  industry: string;
  city: string;
  /** The one thing wrong with this business, in the API's own words. */
  headline_problem: string;
  expected_grade: DemoProfileGrade;
  /** True once this organization holds it, in which case it cannot be imported again. */
  imported: boolean;
  /** The profile it became, set only when `imported` is true. */
  location_id: string | null;
}

export interface DemoProfileList {
  items: DemoProfile[];
}

/**
 * What one import did. `skipped` counts the keys that were already in the organization, so
 * `imported + skipped` is the number of keys that were sent.
 */
/** One profile that was created, paired with the key that asked for it. */
export interface DemoProfileImported {
  key: string;
  location_id: string;
}

export interface DemoProfileImportResult {
  imported: DemoProfileImported[];
  /** Keys already in this workspace. Re-importing one is a no-op, never a duplicate. */
  skipped: string[];
  /** Keys the catalogue no longer has. Reported rather than failing the whole batch. */
  unknown: string[];
}

export const demoProfilesApi = {
  list: () => apiRequest<DemoProfileList>("/demo-profiles"),
  /**
   * Imports the profiles behind these keys. It does not audit them; that is a separate
   * step, and the one that produces anything worth looking at.
   *
   * `projectId` matters more than it looks: the lists that would show the new profiles
   * are project-scoped, so importing without it while a project is active puts them
   * somewhere neither list looks.
   */
  importProfiles: (keys: string[], projectId?: string | null) =>
    apiRequest<DemoProfileImportResult>("/demo-profiles/import", {
      method: "POST",
      body: JSON.stringify({ keys, project_id: projectId ?? null }),
    }),
};
