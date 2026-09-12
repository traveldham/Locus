/**
 * Surfaces the message the API sent. `apiRequest` already puts the API's `detail` on
 * the error, so the person sees what the server actually objected to.
 */
export function apiErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message.trim() ? error.message : fallback;
}
