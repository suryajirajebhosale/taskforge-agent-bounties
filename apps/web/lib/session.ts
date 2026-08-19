export type MeritSession = {
  name: string;
  email: string;
  createdAt: string;
};

const KEY = "merit_session_v1";

export function getSession(): MeritSession | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as MeritSession;
  } catch {
    return null;
  }
}

export function saveSession(session: MeritSession) {
  localStorage.setItem(KEY, JSON.stringify(session));
}

export function clearSession() {
  localStorage.removeItem(KEY);
}
