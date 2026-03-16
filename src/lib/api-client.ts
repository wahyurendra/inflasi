/**
 * HTTP client for calling the FastAPI analytics backend.
 * All database operations go through this client.
 */

const ANALYTICS_URL = process.env.ANALYTICS_API_URL || "http://localhost:8002";
const TIMEOUT_MS = 10_000;

interface ApiClientOptions {
  userId?: string;
  userRole?: string;
  timeout?: number;
}

async function request<T = unknown>(
  method: string,
  path: string,
  options: ApiClientOptions & { body?: unknown; params?: Record<string, string> } = {},
): Promise<T> {
  const url = new URL(`/api${path}`, ANALYTICS_URL);
  if (options.params) {
    for (const [k, v] of Object.entries(options.params)) {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, v);
      }
    }
  }

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (options.userId) headers["X-User-Id"] = options.userId;
  if (options.userRole) headers["X-User-Role"] = options.userRole;

  const resp = await fetch(url.toString(), {
    method,
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
    signal: AbortSignal.timeout(options.timeout ?? TIMEOUT_MS),
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => "Unknown error");
    throw new Error(`API ${method} ${path} failed (${resp.status}): ${text}`);
  }

  return resp.json() as Promise<T>;
}

export const apiClient = {
  get<T = unknown>(path: string, params?: Record<string, string>, opts?: ApiClientOptions) {
    return request<T>("GET", path, { ...opts, params });
  },
  post<T = unknown>(path: string, body?: unknown, opts?: ApiClientOptions) {
    return request<T>("POST", path, { ...opts, body });
  },
  patch<T = unknown>(path: string, body?: unknown, opts?: ApiClientOptions) {
    return request<T>("PATCH", path, { ...opts, body });
  },
  delete<T = unknown>(path: string, opts?: ApiClientOptions) {
    return request<T>("DELETE", path, opts);
  },
};
