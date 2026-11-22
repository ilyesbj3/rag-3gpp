// fetch wrappers with timeout and error mapping (UI_SPEC.md §6).
export class ApiError extends Error {
  constructor(status, code, message, fix) {
    super(message);
    this.status = status;
    this.code = code;
    this.fix = fix || null;
  }
}

const TIMEOUT_MS = 120000;

export async function request(path, { method = "GET", body, timeout = TIMEOUT_MS } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeout);
  let res;
  try {
    res = await fetch(path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
  } catch (err) {
    clearTimeout(timer);
    if (err.name === "AbortError") {
      throw new ApiError(0, "timeout", "The server took more than 2 minutes to answer.", null);
    }
    throw new ApiError(0, "network", "Cannot reach the server.",
      "uvicorn app.server:app --host 127.0.0.1 --port 8000");
  }
  clearTimeout(timer);
  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    const e = (data && data.error) || {};
    throw new ApiError(res.status, e.code || "http_" + res.status,
      e.message || `Request failed (HTTP ${res.status}).`, e.fix || null);
  }
  return data;
}

export const api = {
  health: () => request("/api/health", { timeout: 15000 }),
  examples: () => request("/api/examples", { timeout: 15000 }),
  evaluation: () => request("/api/eval", { timeout: 15000 }),
  ask: (payload) => request("/api/ask", { method: "POST", body: payload }),
};
