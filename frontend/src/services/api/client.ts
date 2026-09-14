const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "locus_access_token";

interface RefreshResponse {
  access_token: string;
}

let refreshRequest: Promise<string | null> | null = null;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    /**
     * The parsed `detail` exactly as the API sent it. Most endpoints send a string, which
     * `message` already carries; the ones that reject on contents send an object with
     * `field_errors`, and only the caller knows how to word those per field.
     */
    public detail?: unknown,
  ) {
    super(message);
  }
}

/** The sentence to show, from a `detail` that may be a string or a structured object. */
function errorMessage(body: { detail?: unknown; message?: unknown } | null) {
  const detail = body?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (detail && typeof detail === "object") {
    const nested = (detail as { message?: unknown }).message;
    if (typeof nested === "string" && nested) return nested;
  }
  if (typeof body?.message === "string" && body.message) return body.message;
  return "Something went wrong. Please try again.";
}

export function getAccessToken() {
  return typeof window === "undefined"
    ? null
    : window.localStorage.getItem(TOKEN_KEY);
}

export function setAccessToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshRequest) {
    refreshRequest = fetch(`${API_URL}/auth/refresh`, {
      method: "POST",
      credentials: "include",
    })
      .then(async (response) => {
        if (!response.ok) return null;
        const body = (await response.json()) as RefreshResponse;
        setAccessToken(body.access_token);
        return body.access_token;
      })
      .catch(() => null)
      .finally(() => {
        refreshRequest = null;
      });
  }
  return refreshRequest;
}

async function request(path: string, init: RequestInit, token: string | null) {
  return fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
}

/**
 * One authenticated call, as the raw `Response`.
 *
 * `apiRequest` is this plus JSON parsing and is what almost everything should use. This
 * exists for the one response that is not JSON and must not be buffered: the agent's
 * `text/event-stream`, which is read incrementally from `response.body`. Going through here
 * rather than calling `fetch` directly is what keeps the bearer token, the refresh-once-on-
 * 401 retry and the error shape in a single place — `EventSource` cannot send an
 * `Authorization` header at all, which is why the stream is a `fetch` in the first place.
 */
export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const token = getAccessToken();
  let response = await request(path, init, token);

  if (
    response.status === 401 &&
    path !== "/auth/refresh" &&
    path !== "/auth/login"
  ) {
    const refreshedToken = await refreshAccessToken();
    if (refreshedToken) response = await request(path, init, refreshedToken);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    if (response.status === 401) setAccessToken(null);
    throw new ApiError(errorMessage(body), response.status, body?.detail);
  }

  return response;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await apiFetch(path, init);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
