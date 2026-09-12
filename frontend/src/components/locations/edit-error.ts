import { ApiError } from "@/services/api/client";

export interface EditErrorCopy {
  title: string;
  description: string;
}

/**
 * A 502 means the request reached Google and Google refused it, which is a very
 * different thing for the person editing than Locus failing to respond.
 */
export function describeEditError(error: unknown, fallbackTitle: string): EditErrorCopy {
  if (error instanceof ApiError) {
    if (error.status === 502) {
      return {
        title: "Google rejected this change",
        description:
          error.message ||
          "Google would not accept these values for this profile. Adjust them and try again.",
      };
    }
    return { title: fallbackTitle, description: error.message };
  }

  return {
    title: fallbackTitle,
    description:
      error instanceof Error && error.message
        ? error.message
        : "The request to Locus did not complete. Check your connection, then try again.",
  };
}
