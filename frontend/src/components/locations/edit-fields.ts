import { humanizeToken } from "./hours-model";

/** The request fields the profile editor can send, in the order the form shows them. */
export const EDIT_FIELD_LABELS: Record<string, string> = {
  title: "Business name",
  open_status: "Open status",
  phone_primary: "Phone",
  website_uri: "Website",
  description: "Description",
  hours: "Opening hours",
};

/**
 * The API is free to name a field the client does not know about, so an unknown key
 * is shown in a readable form rather than hidden.
 */
export function editFieldLabel(field: string) {
  return EDIT_FIELD_LABELS[field] ?? humanizeToken(field);
}
