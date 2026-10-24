const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const REQUEST_TIMEOUT_MS = 20_000;

export type FieldErrors = Record<string, string[]>;

export class ApiError extends Error {
  status: number;
  code: string;
  fieldErrors: FieldErrors;

  constructor(
    status: number,
    code: string,
    message: string,
    fieldErrors: FieldErrors = {},
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

// The access token lives only in memory; the refresh token is an HttpOnly cookie.
let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
  /** Attach the access token and transparently refresh it once on 401. */
  auth?: boolean;
  signal?: AbortSignal;
};

type Envelope<T> = { success: boolean; data?: T; message?: string };

async function send<T>(path: string, options: RequestOptions): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  options.signal?.addEventListener("abort", () => controller.abort());

  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (options.auth && accessToken) headers.Authorization = `Bearer ${accessToken}`;

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      credentials: "include",
      signal: controller.signal,
    });
  } catch {
    const timedOut = controller.signal.aborted && !options.signal?.aborted;
    throw new ApiError(
      0,
      timedOut ? "TIMEOUT" : "NETWORK_ERROR",
      timedOut
        ? "The server took too long to respond. Please try again."
        : "Cannot reach the server. Check your connection and try again.",
    );
  } finally {
    window.clearTimeout(timer);
  }

  if (response.status === 204) return undefined as T;

  let payload: (Envelope<T> & { code?: string; errors?: FieldErrors }) | null = null;
  try {
    payload = await response.json();
  } catch {
    // Non-JSON body (e.g. a proxy error page): fall through to the generic error.
  }

  if (!response.ok || !payload?.success) {
    throw new ApiError(
      response.status,
      payload?.code ?? "UNKNOWN_ERROR",
      payload?.message ?? "Something went wrong. Please try again.",
      payload?.errors ?? {},
    );
  }
  return payload.data as T;
}

type SessionTokens = { access: string };

let refreshInFlight: Promise<string | null> | null = null;

/**
 * Exchange the refresh cookie for a new access token. Concurrent callers share one
 * request: refresh tokens are single-use, so a second parallel call would look like
 * token theft to the server and end the session.
 * Resolves null when there is no valid session; rejects on network/server failure.
 */
export function refreshAccessToken(): Promise<string | null> {
  refreshInFlight ??= send<SessionTokens>("/auth/refresh/", { method: "POST" })
    .then((data) => {
      accessToken = data.access;
      return data.access;
    })
    .catch((error: unknown) => {
      if (error instanceof ApiError && error.status === 401) {
        accessToken = null;
        return null;
      }
      throw error;
    })
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  try {
    return await send<T>(path, options);
  } catch (error) {
    const expired =
      options.auth &&
      error instanceof ApiError &&
      error.status === 401 &&
      (error.code === "AUTHENTICATION_FAILED" || error.code === "NOT_AUTHENTICATED");
    if (!expired) throw error;
    if (!(await refreshAccessToken())) throw error;
    return send<T>(path, options);
  }
}
