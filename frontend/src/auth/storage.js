export const AUTH_SESSION_STORAGE_KEY = "siged-pnp.auth.session";
export const LEGACY_UPLOAD_TOKEN_STORAGE_KEY = "siged-pnp.cargas.token";

const SESSION_EXPIRY_LEEWAY_MS = 30_000;

function isBrowser() {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function isValidUser(user) {
  return Boolean(
    user &&
      typeof user === "object" &&
      typeof user.username === "string" &&
      typeof user.rol_codigo === "string"
  );
}

export function buildAuthSession(payload) {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const accessToken = payload.access_token ?? payload.accessToken ?? "";
  const tokenType = payload.token_type ?? payload.tokenType ?? "bearer";
  const expiresIn = Number(payload.expires_in ?? payload.expiresIn ?? 0);
  const expiresAtCandidate = Number(payload.expiresAt ?? 0);
  const expiresAt =
    Number.isFinite(expiresAtCandidate) && expiresAtCandidate > 0
      ? expiresAtCandidate
      : expiresIn > 0
        ? Date.now() + expiresIn * 1000
        : 0;
  const user = payload.user ?? null;

  if (!accessToken || !isValidUser(user) || !expiresAt) {
    return null;
  }

  return {
    accessToken,
    tokenType,
    expiresIn,
    expiresAt,
    user
  };
}

export function readStoredAuthSession() {
  if (!isBrowser()) {
    return null;
  }

  const rawSession = window.localStorage.getItem(AUTH_SESSION_STORAGE_KEY);
  if (!rawSession) {
    return null;
  }

  try {
    const session = buildAuthSession(JSON.parse(rawSession));
    if (!session) {
      clearStoredAuthSession();
    }
    return session;
  } catch {
    clearStoredAuthSession();
    return null;
  }
}

export function persistAuthSession(payload) {
  const session = buildAuthSession(payload);
  if (!session) {
    return null;
  }

  if (isBrowser()) {
    window.localStorage.setItem(AUTH_SESSION_STORAGE_KEY, JSON.stringify(session));
    window.localStorage.removeItem(LEGACY_UPLOAD_TOKEN_STORAGE_KEY);
  }

  return session;
}

export function clearStoredAuthSession() {
  if (!isBrowser()) {
    return;
  }

  window.localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  window.localStorage.removeItem(LEGACY_UPLOAD_TOKEN_STORAGE_KEY);
}

export function isAuthSessionExpired(session, leewayMs = SESSION_EXPIRY_LEEWAY_MS) {
  if (!session?.expiresAt) {
    return true;
  }

  return Number(session.expiresAt) <= Date.now() + leewayMs;
}
