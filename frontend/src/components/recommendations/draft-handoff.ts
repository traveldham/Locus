/**
 * Hands an audit's drafted value to the location editor in the same browser.
 *
 * sessionStorage, not the URL: a description can be 750 characters, and the draft must
 * not survive into another tab or another day. The editor takes it once and clears it.
 */

export interface DraftHandoff {
  field: "title" | "description";
  value: string;
  reason: string;
}

const key = (locationId: string) => `locus:audit-draft:${locationId}`;

export function storeDraft(locationId: string, draft: DraftHandoff) {
  try {
    sessionStorage.setItem(key(locationId), JSON.stringify(draft));
  } catch {
    // Storage may be unavailable; the editor simply opens without the draft.
  }
}

export function takeDraft(locationId: string): DraftHandoff | null {
  try {
    const raw = sessionStorage.getItem(key(locationId));
    if (!raw) return null;
    sessionStorage.removeItem(key(locationId));
    const parsed = JSON.parse(raw) as Partial<DraftHandoff>;
    if (
      (parsed.field === "title" || parsed.field === "description") &&
      typeof parsed.value === "string"
    ) {
      return {
        field: parsed.field,
        value: parsed.value,
        reason: typeof parsed.reason === "string" ? parsed.reason : "",
      };
    }
    return null;
  } catch {
    return null;
  }
}
