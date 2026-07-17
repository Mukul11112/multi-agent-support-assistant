// Thin client over the FastAPI backend. Token lives in localStorage, which is
// fine for this project but is worth naming as a tradeoff in your report: it is
// readable by any XSS on the page. httpOnly cookies avoid that, at the cost of
// CSRF handling and a same-site deployment.

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const TOKEN_KEY = 'techmart_token';
const USER_KEY = 'techmart_user';

export const auth = {
  token: () => (typeof window === 'undefined' ? null : localStorage.getItem(TOKEN_KEY)),
  user: () => {
    if (typeof window === 'undefined') return null;
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  save: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clear: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

async function request(path, { method = 'GET', body, authed = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (authed) {
    const token = auth.token();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    // fetch only rejects on network failure, so this is the "backend is down"
    // case, not a 4xx/5xx.
    throw new Error(`Cannot reach the server at ${BASE}. Is the backend running?`);
  }

  if (res.status === 401 && authed) {
    auth.clear();
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Your session expired. Please sign in again.');
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    // FastAPI returns detail as a string (HTTPException) or as an array of
    // validation errors (422). Handle both so users never see "[object Object]".
    const detail = data.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(', ')
      : detail || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  register: (email, password, name) =>
    request('/auth/register', { method: 'POST', body: { email, password, name }, authed: false }),
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: { email, password }, authed: false }),
  me: () => request('/auth/me'),

  chat: (message, sessionId) =>
    request('/chat', { method: 'POST', body: { message, session_id: sessionId } }),
  sessions: () => request('/chat/sessions'),
  history: (sessionId) => request(`/chat/history/${sessionId}`),
  deleteSession: (sessionId) => request(`/chat/history/${sessionId}`, { method: 'DELETE' }),

  analytics: () => request('/analytics'),
  health: () => request('/health', { authed: false }),
};
