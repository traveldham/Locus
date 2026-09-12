import { ApiError } from "@/services/api/client";

export type ReviewAction = "reply" | "remove_reply" | "sync";

/**
 * A 502 means Locus reached Google and Google refused the call, which is a very
 * different thing to tell someone than "something went wrong".
 */
const GOOGLE_REJECTED: Record<ReviewAction, string> = {
  reply: "Google rejected this reply, so nothing was published. Your draft is still here.",
  remove_reply: "Google rejected removing this reply, so it is still published.",
  sync: "Google rejected the sync request. Check the connection, then try again.",
};

const UNREACHABLE: Record<ReviewAction, string> = {
  reply: "The reply did not reach Locus. Your draft is still here — check your connection and try again.",
  remove_reply: "The request did not reach Locus. Check your connection, then try again.",
  sync: "The sync request did not reach Locus. Check your connection, then try again.",
};

export function reviewErrorMessage(error: unknown, action: ReviewAction): string {
  if (error instanceof ApiError) {
    if (error.status === 502) return GOOGLE_REJECTED[action];
    return error.message;
  }
  return UNREACHABLE[action];
}
