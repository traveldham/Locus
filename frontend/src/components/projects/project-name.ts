/**
 * The API trims a project name and then requires 2 to 160 characters, so the client
 * checks the same rule before sending anything.
 */
export const PROJECT_NAME_MIN_LENGTH = 2;
export const PROJECT_NAME_MAX_LENGTH = 160;

/** Returns null when the name is acceptable, otherwise the message to show. */
export function projectNameError(value: string): string | null {
  const name = value.trim();
  if (name.length === 0) return "Enter a project name.";
  if (name.length < PROJECT_NAME_MIN_LENGTH) {
    return `Use at least ${PROJECT_NAME_MIN_LENGTH} characters.`;
  }
  if (name.length > PROJECT_NAME_MAX_LENGTH) {
    return `Use ${PROJECT_NAME_MAX_LENGTH} characters or fewer. This name has ${name.length}.`;
  }
  return null;
}
