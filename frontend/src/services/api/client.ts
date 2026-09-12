const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "locus_access_token";

interface RefreshResponse {
  access_token: string;
}

let refreshRequest: Promise<string | null> | null = null;

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export function getAccessToken() {
  return typeof window === "undefined" ? null : window.localStorage.getItem(TOKEN_KEY);
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

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getAccessToken();
  let response = await request(path, init, token);

  if (response.status === 401 && path !== "/auth/refresh" && path !== "/auth/login") {
    const refreshedToken = await refreshAccessToken();
    if (refreshedToken) response = await request(path, init, refreshedToken);
  }

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    if (response.status === 401) setAccessToken(null);
    throw new ApiError(
      body?.detail ?? body?.message ?? "Something went wrong. Please try again.",
      response.status,
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
