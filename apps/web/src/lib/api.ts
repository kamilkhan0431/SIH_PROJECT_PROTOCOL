export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function authHeader(): HeadersInit {
  if (typeof window === "undefined") return {};
  const t = localStorage.getItem("ss_token");
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { headers: { ...authHeader() }, cache: "no-store" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type SessionUser = {
  username: string;
  role: "citizen" | "field" | "district" | "sdma" | string;
  display_name: string;
  district: string;
};

export function readSession(): { token: string; user: SessionUser } | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("ss_token");
  const raw = localStorage.getItem("ss_user");
  if (!token || !raw) return null;
  return { token, user: JSON.parse(raw) };
}

export function writeSession(token: string, user: SessionUser) {
  localStorage.setItem("ss_token", token);
  localStorage.setItem("ss_user", JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem("ss_token");
  localStorage.removeItem("ss_user");
}
