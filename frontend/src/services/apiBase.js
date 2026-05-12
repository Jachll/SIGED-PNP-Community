const LOCAL_API_BASE_URL = "http://localhost:8000";

export function resolveApiBaseUrl(rawValue, { isDev = false } = {}) {
  const normalizedValue = typeof rawValue === "string" ? rawValue.trim() : "";

  if (normalizedValue) {
    return normalizedValue;
  }

  return isDev ? LOCAL_API_BASE_URL : "";
}
