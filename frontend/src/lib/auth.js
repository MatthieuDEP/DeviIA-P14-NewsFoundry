export const TOKEN_KEY = "access_token";

export async function apiRequest(path, options = {}, timeout = 10000) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) throw new Error("Le service est temporairement indisponible.");

  let response;
  let data;
  try {
    response = await fetch(`${apiUrl.replace(/\/$/, "")}${path}`, {
      ...options,
      cache: "no-store",
      signal: options.signal
        ? AbortSignal.any([options.signal, AbortSignal.timeout(timeout)])
        : AbortSignal.timeout(timeout),
    });
    data = await response.json();
  } catch {
    throw new Error("Impossible de joindre le service. Vérifiez votre connexion et réessayez.");
  }
  if (!response.ok) {
    const error = new Error(
      [401, 404, 409, 422, 429, 502, 503, 504].includes(response.status) && typeof data?.detail === "string"
        ? data.detail
        : "Le service est temporairement indisponible.",
    );
    error.status = response.status;
    throw error;
  }
  return data;
}

export async function login(email, password) {
  const data = await apiRequest("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email.trim(), password }),
  });
  if (!data || typeof data.access_token !== "string" || !data.access_token) {
    throw new Error("La connexion a échoué. Réessayez.");
  }
  try {
    localStorage.setItem(TOKEN_KEY, data.access_token);
  } catch {
    throw new Error("Votre navigateur ne permet pas d’enregistrer la connexion.");
  }
}

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    throw new Error("Votre navigateur ne permet pas de retrouver la connexion.");
  }
}

export function logout() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function getUser(token) {
  const user = await apiRequest("/me", { headers: { Authorization: `Bearer ${token}` } });
  if (!user || !Number.isSafeInteger(user.id) || user.id < 1 || typeof user.email !== "string") {
    throw new Error("Le service est temporairement indisponible.");
  }
  return user;
}
