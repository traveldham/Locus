import { ApiError } from "@/services/api/client";

/**
 * What to put in front of a reader when something failed.
 *
 * Two things make the raw message unsafe to render. A validation failure arrives with an
 * array `detail`, which the shared client stringifies into `[object Object]` noise; and a
 * status the agent has its own meaning for — a conflict is "still working", not an error
 * the reader caused — reads better in the product's own words.
 */
export function agentErrorMessage(
  error: Error | null | undefined,
  fallback: string,
): string {
  if (!error) return fallback;

  if (error instanceof ApiError) {
    if (error.status === 409) {
      return "The assistant is still working on your last message. It will answer shortly.";
    }
    if (error.status === 404) {
      return "This conversation is no longer available. Start a new chat to carry on.";
    }
    if (error.status === 403) {
      // Scope-neutral: the same 403 can come back for a location or for a project.
      return "You do not have access to these conversations.";
    }
    if (error.status >= 500) {
      return "The assistant is not responding right now. Try again in a moment.";
    }
  }

  const message = typeof error.message === "string" ? error.message.trim() : "";
  if (!message || message.includes("[object")) return fallback;
  return message;
}
