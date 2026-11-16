import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { authApi, clearSession, getAccessToken, getRefreshToken, saveSession, type TokenResponse } from "../lib/api";

type AuthUser = TokenResponse["user"];
type AuthContextValue = { user: AuthUser | null; loading: boolean; login: (email: string, password: string) => Promise<void>; logout: () => Promise<void>; };
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let active = true;
    async function load() {
      if (!getAccessToken()) { if (active) setLoading(false); return; }
      try { const current = await authApi.me(); if (active) setUser(current); }
      catch { clearSession(); if (active) setUser(null); }
      finally { if (active) setLoading(false); }
    }
    void load();
    return () => { active = false; };
  }, []);
  const value = useMemo<AuthContextValue>(() => ({
    user, loading,
    async login(email, password) {
      const result = await authApi.login({email, password});
      saveSession(result.access_token, result.refresh_token);
      setUser(result.user);
    },
    async logout() {
      const refresh = getRefreshToken();
      try { if (refresh) await authApi.logout(refresh); }
      finally { clearSession(); setUser(null); }
    }
  }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
