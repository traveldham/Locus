"use client";

import { locationKeys } from "@/hooks/use-locations";
import { auditDirectoryKey } from "@/hooks/use-recommendations";
import { demoProfilesApi } from "@/services/api/demo-profiles";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export const demoProfileKeys = {
  all: ["demo-profiles"] as const,
  list: () => [...demoProfileKeys.all, "list"] as const,
};

/**
 * The sample catalogue the API offers. It is small and changes only when something is
 * imported, so it is read once per visit to the picker rather than polled.
 */
export function useDemoProfilesQuery() {
  return useQuery({
    queryKey: demoProfileKeys.list(),
    queryFn: demoProfilesApi.list,
    retry: 1,
    staleTime: 60_000,
  });
}

/**
 * Imports sample profiles into the organization. No audit is run, so nothing about an
 * existing report changes — but every list of profiles has new rows, and the catalogue
 * itself now marks what was imported.
 */
export function useImportDemoProfilesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ keys, projectId }: { keys: string[]; projectId?: string | null }) =>
      demoProfilesApi.importProfiles(keys, projectId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: demoProfileKeys.all }),
        queryClient.invalidateQueries({ queryKey: locationKeys.all }),
        // The audit directory lists every profile, audited or not.
        queryClient.invalidateQueries({ queryKey: auditDirectoryKey }),
      ]);
    },
  });
}
