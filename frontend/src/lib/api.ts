const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const ACCESS_TOKEN_KEY = "nexus.access_token";
const REFRESH_TOKEN_KEY = "nexus.refresh_token";

export type ApiErrorBody = { detail?: string | Array<{ msg?: string; loc?: (string | number)[] }> };

export class ApiError extends Error {
  status: number;
  body: ApiErrorBody | null;

  constructor(status: number, message: string, body: ApiErrorBody | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer" | string;
  user: {
    id: string;
    email: string;
    full_name: string;
    is_active: boolean;
  };
};

export function saveSession(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

export function clearSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

async function readError(response: Response): Promise<ApiError> {
  let body: ApiErrorBody | null = null;
  let message = `Request failed (${response.status})`;
  try {
    body = await response.json() as ApiErrorBody;
    if (typeof body.detail === "string") message = body.detail;
    else if (Array.isArray(body.detail)) {
      message = body.detail.map(item => item.msg ?? "Invalid value").join(", ");
    }
  } catch {
    // Keep the status-based fallback when the response isn't JSON.
  }
  return new ApiError(response.status, message, body);
}

let refreshInFlight: Promise<boolean> | null = null;

async function refreshSession(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (!response.ok) {
          clearSession();
          return false;
        }
        const tokens = await response.json() as TokenResponse;
        saveSession(tokens.access_token, tokens.refresh_token);
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const send = () => {
    const headers = new Headers(init.headers);
    if (!(init.body instanceof FormData) && init.body !== undefined && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
    return fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  };

  let response = await send();
  if (response.status === 401 && !path.endsWith("/auth/login") && !path.endsWith("/auth/refresh")) {
    const refreshed = await refreshSession();
    if (refreshed) response = await send();
    else clearSession();
  }

  if (!response.ok) throw await readError(response);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const healthCheck = () =>
  apiRequest<{ status: string; database?: string }>("/health/database");

export const authApi = {
  login: (payload: { email: string; password: string }) =>
    apiRequest<TokenResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify(payload) }),
  me: () => apiRequest<TokenResponse["user"]>("/api/v1/auth/me"),
  logout: (refresh_token: string) =>
    apiRequest<void>("/api/v1/auth/logout", { method: "POST", body: JSON.stringify({ refresh_token }) })
};
