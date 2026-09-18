const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const TOKEN_KEY = "omnicalc-access-token";

let accessToken = sessionStorage.getItem(TOKEN_KEY) || "";

export function setAccessToken(token) {
  accessToken = token || "";
  if (accessToken) sessionStorage.setItem(TOKEN_KEY, accessToken);
  else sessionStorage.removeItem(TOKEN_KEY);
}

function errorMessage(data, fallback) {
  const detail = data?.detail;
  const questions = Array.isArray(detail?.questions) ? detail.questions.join(" ") : "";
  if (typeof detail === "string") return detail;
  return questions || detail?.message || fallback;
}

async function rawRequest(path, options = {}) {
  const headers = { ...(options.body ? { "Content-Type": "application/json" } : {}), ...options.headers };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  return fetch(`${API_BASE_URL}${path}`, { ...options, headers, credentials: "include" });
}

async function request(path, options = {}, retry = true) {
  let response = await rawRequest(path, options);
  if (response.status === 401 && retry && path !== "/api/v1/auth/refresh") {
    const refreshed = await refreshSession(false);
    if (refreshed) response = await rawRequest(path, options);
  }
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new Error(errorMessage(data, "The request could not be completed."));
  return data;
}

export async function registerAccount(payload) {
  const data = await request("/api/v1/auth/register", { method: "POST", body: JSON.stringify(payload) }, false);
  setAccessToken(data.access_token);
  return data;
}

export async function loginAccount(payload) {
  const data = await request("/api/v1/auth/login", { method: "POST", body: JSON.stringify(payload) }, false);
  setAccessToken(data.access_token);
  return data;
}

export async function loginWithGoogle(credential) {
  const data = await request("/api/v1/auth/google", { method: "POST", body: JSON.stringify({ credential }) }, false);
  setAccessToken(data.access_token);
  return data;
}

export async function refreshSession(throwOnFailure = true) {
  try {
    const data = await request("/api/v1/auth/refresh", { method: "POST" }, false);
    setAccessToken(data.access_token);
    return data;
  } catch (error) {
    setAccessToken("");
    if (throwOnFailure) throw error;
    return null;
  }
}

export async function logoutAccount() {
  try {
    await request("/api/v1/auth/logout", { method: "POST" }, false);
  } finally {
    setAccessToken("");
  }
}

export function getCurrentUser() { return request("/api/v1/auth/me"); }

export function calculate(query, calculator) {
  return request("/api/v1/calculate", {
    method: "POST",
    body: JSON.stringify({ query, calculator: calculator || null }),
  });
}

export function getHistory() { return request("/api/v1/history?limit=50"); }
export function clearRemoteHistory() { return request("/api/v1/history", { method: "DELETE" }); }

export function saveWorkflow(name, description, workflowDefinition) {
  return request("/api/v1/workflows", {
    method: "POST",
    body: JSON.stringify({ name, description, workflow_definition: workflowDefinition }),
  });
}

export function getWorkflows() { return request("/api/v1/workflows"); }
export function deleteWorkflow(workflowId) { return request(`/api/v1/workflows/${workflowId}`, { method: "DELETE" }); }
