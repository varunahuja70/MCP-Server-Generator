/**
 * MCP Forge API client with strict error handling, session management,
 * and automatic X-Forge-Request: 1 header.
 */

export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  hint?: string;
  field?: string;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details?: Record<string, unknown>;
  readonly hint?: string;
  readonly field?: string;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message || `API Error ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.code = payload.code || "UNKNOWN_ERROR";
    this.details = payload.details;
    this.hint = payload.hint;
    this.field = payload.field;
  }
}

const API_BASE = "";

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});

  // Mandatory CSRF protection header on state changes & requests
  headers.set("X-Forge-Request", "1");
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }

  // Set Content-Type for JSON body if not set
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "same-origin",
  });

  if (!response.ok) {
    let payload: ApiErrorPayload;
    try {
      const json = await response.json();
      payload = json.error || json;
    } catch {
      payload = {
        code: "HTTP_ERROR",
        message: response.statusText || `Request failed with status ${response.status}`,
      };
    }
    throw new ApiError(response.status, payload);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json() as Promise<T>;
  }

  return response.text() as Promise<unknown> as Promise<T>;
}
