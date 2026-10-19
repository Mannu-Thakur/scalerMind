export type User = {
  id: string;
  email: string;
  display_name: string;
  role: "learner" | "admin";
  is_active: boolean;
};

export type AuthResult = {
  access_token: string;
  token_type: "bearer";
  user: User;
};

export function csrfToken(): string {
  const cookieName = "scalermind_csrf=";
  const cookie = document.cookie
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(cookieName));
  return cookie ? decodeURIComponent(cookie.slice(cookieName.length)) : "";
}

async function requestAuthentication(
  path: "login" | "signup" | "refresh",
  payload?: Record<string, string>,
): Promise<AuthResult> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (path === "refresh") headers["X-CSRF-Token"] = csrfToken();

  const response = await fetch(`/api/auth/${path}`, {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers,
    ...(payload ? { body: JSON.stringify(payload) } : {}),
  });
  const body = (await response.json().catch(() => ({}))) as {
    detail?: string | Array<{ msg?: string }>;
  } & Partial<AuthResult>;

  if (!response.ok || !body.access_token || !body.user) {
    const message = Array.isArray(body.detail)
      ? body.detail.map((issue) => issue.msg).filter(Boolean).join("; ")
      : body.detail;
    throw new Error(message || "Unable to sign in. Please try again.");
  }
  return body as AuthResult;
}

let refreshInFlight: Promise<AuthResult> | null = null;

export function authenticate(
  path: "login" | "signup" | "refresh",
  payload?: Record<string, string>,
): Promise<AuthResult> {
  if (path !== "refresh") return requestAuthentication(path, payload);
  if (refreshInFlight) return refreshInFlight;

  const renew = () => requestAuthentication("refresh");
  const renewal = navigator.locks
    ? navigator.locks.request("scalermind-refresh-session", renew)
    : renew();
  refreshInFlight = renewal.finally(() => {
    refreshInFlight = null;
  });
  return refreshInFlight;
}

export async function endSession(): Promise<void> {
  await fetch("/api/auth/logout", {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": csrfToken() },
  });
}
